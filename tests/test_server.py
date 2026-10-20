import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from habilin.intents import classify
from habilin.narrate import phrase
from habilin.server import make_server
from habilin.core import Principal, digest


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = make_server(self.temp.name, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, body=None, role="operator", **headers):
        data = None if body is None else json.dumps(body).encode()
        auth = {"Content-Type":"application/json"}
        if role:
            auth["Authorization"] = "Bearer " + self.server.tokens[role]
        req = urllib.request.Request(self.url+path, data=data, headers={**auth, **headers})
        try:
            res = urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:
            res = exc
        return res.status, res.read()

    def test_state_needs_authentication(self):
        self.assertEqual(self.request("/api/state",role=None)[0],403)
        self.assertEqual(self.request("/api/state",role=None,Authorization="Bearer é")[0],403)

    def test_request_body_cannot_claim_owner_role(self):
        status,_=self.request("/api/message",{"text":"Progress this estate case","role":"owner"})
        self.assertEqual(status,400)

    def test_http_tool_bypass_is_rejected(self):
        operator=Principal("demo-operator","operator","EST-001")
        professional=Principal("demo-cpa","professional","EST-001")
        self.server.agent.tool(operator,"answer_question",answer=False)
        case=self.server.agent.advance(operator)
        packet_hash=digest(case["packet"])
        self.server.agent.tool(professional,"professional_approve",packet_hash=packet_hash,confirmed=True)
        code=self.server.agent.issue_code()
        status,_=self.request("/api/tool",{"name":"owner_approve","args":{"confirmed":True,"code":code,"packet_hash":packet_hash}})
        self.assertEqual(status,400)
        self.assertEqual(self.request("/api/tool",{"name":"lock","args":{}})[0],400)
        case=self.server.agent.view(operator)
        self.assertEqual(case["stage"],"await_owner")
        self.assertFalse(case["locked"])
        self.assertIsNone(case["owner_hash"])

    def test_secrets_and_other_case_are_not_routes(self):
        for path in ["/.runtime/access.json","/api/cases/OTHER","/api/code","/../AGENTS.md"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0],404)
        _,raw=self.request("/api/state")
        for token in self.server.tokens.values():
            self.assertNotIn(token.encode(),raw)

    def test_origin_and_host_are_checked(self):
        self.assertEqual(self.request("/api/state",Origin="https://attacker.invalid")[0],403)
        self.assertEqual(self.request("/api/state",Host="attacker.invalid")[0],403)

    def test_taglish_progress_runs_real_tools(self):
        status,raw=self.request("/api/message",{"text":"Asikasuhin mo ang estate case"})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(raw)["classification"]["source"],"offline_fixture")
        self.assertIn("family home",json.loads(raw)["reply"])
        self.assertEqual(json.loads(self.request("/api/state")[1])["case"]["stage"],"ready_to_prepare")
        self.assertEqual(self.request("/api/tool",{"name":"answer_question","args":{"answer":False}})[0],200)
        self.request("/api/message",{"text":"Progress this estate case"})
        self.assertEqual(json.loads(self.request("/api/state")[1])["case"]["stage"],"await_professional")

    def test_case_header_selects_uk_case_and_rejects_unknown(self):
        case=json.loads(self.request("/api/state",**{"X-Case-Id":"EST-UK-001"})[1])["case"]
        self.assertEqual(case["jurisdiction"],"UK")
        self.assertEqual(self.request("/api/state",**{"X-Case-Id":"EST-999"})[0],403)

    def test_clarification_correction_and_off_topic_do_not_mutate_case(self):
        before=json.loads(self.request("/api/state")[1])["case"]["stage"]
        for text,intent in [("yes","unclear"),("The ownership share is wrong","correction"),("What is the weather","off_topic")]:
            status,raw=self.request("/api/message",{"text":text})
            self.assertEqual(status,200)
            self.assertEqual(json.loads(raw)["classification"]["intent"],intent)
        self.assertEqual(json.loads(self.request("/api/state")[1])["case"]["stage"],before)
        status,raw=self.request("/api/message",{"text":"Explain the tax"})
        self.assertEqual(status,200)
        self.assertIn("not prepared yet",json.loads(raw)["reply"])


class IntentTests(unittest.TestCase):
    def test_otp_never_reaches_model(self):
        with patch("habilin.intents.subprocess.run") as call:
            for text in ["My OTP is 123456","OTP123456","123456a","My code is 123 456","Code: 123-456"]:
                self.assertEqual(classify(text,live=True)["intent"],"unsafe")
            call.assert_not_called()

    def test_missing_model_does_not_fall_back_to_execution(self):
        with patch("habilin.intents.subprocess.run",side_effect=FileNotFoundError):
            self.assertEqual(classify("Progress this estate case",live=True),{"intent":"unclear","source":"model_unavailable"})

    def test_invalid_or_low_confidence_model_response_requires_clarification(self):
        for result in [{"classification":"pay_tax","decision":"auto","id":"message","probabilities":{"pay_tax":1}},
                       {"classification":"progress","decision":"review","id":"message","probabilities":{"progress":.6,"unclear":.4}}]:
            mock=type("Result",(),{"stdout":json.dumps({"provider":"typesafe","results":[result]})})()
            with patch("habilin.intents.subprocess.run",return_value=mock):
                self.assertEqual(classify("Do something",live=True)["intent"],"unclear")


class PhrasingTests(unittest.TestCase):
    facts = "Filing is verified. The PHP 150,000 payment is pending."

    def model_says(self, text):
        body = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
        response = type("Response", (), {"read": lambda self, *a: body, "__enter__": lambda self: self, "__exit__": lambda self, *a: None})()
        return patch("habilin.narrate.urllib.request.urlopen", return_value=response)

    def test_without_key_returns_fixed_reply_and_no_call(self):
        with patch.dict("os.environ", {}, clear=True), patch("habilin.narrate.urllib.request.urlopen") as call:
            self.assertEqual(phrase(self.facts, "status?"), (self.facts, None))
            call.assert_not_called()

    def test_grounded_rewording_is_used(self):
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}), self.model_says("Na-file na. Pending pa ang PHP 150,000 na bayad."):
            self.assertEqual(phrase(self.facts, "kumusta?")[0], "Na-file na. Pending pa ang PHP 150,000 na bayad.")

    def test_invented_number_or_contact_falls_back(self):
        for text in ["You paid PHP 15,000.", "Send it to help@example.com.", "Pay at https://pay.example"]:
            with self.subTest(text=text), patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}), self.model_says(text):
                self.assertEqual(phrase(self.facts, "status?"), (self.facts, None))

    def test_model_failure_falls_back(self):
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}), \
             patch("habilin.narrate.urllib.request.urlopen", side_effect=OSError):
            self.assertEqual(phrase(self.facts, "status?"), (self.facts, None))
