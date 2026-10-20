import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from habilin.intents import classify
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
        self.assertEqual(json.loads(self.request("/api/state")[1])["case"]["stage"],"await_professional")

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
