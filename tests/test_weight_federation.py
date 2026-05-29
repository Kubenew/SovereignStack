import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATA_DIR"] = "./data_test"
os.environ["NODE_ID"] = "test-weight-node"

from services.weight_federation_service import app

client = TestClient(app)


def clean_shards():
    for f in ["shard_manifest.json"]:
        p = os.path.join("data_test", f)
        if os.path.exists(p):
            os.remove(p)
    import glob
    for f in glob.glob("data_test/shards/*.enc"):
        os.remove(f)


@pytest.fixture(autouse=True)
def setup():
    clean_shards()
    yield
    clean_shards()


class TestHealth:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert d["service"] == "weight_federation"


class TestShardRegistration:
    def test_register_shard(self):
        r = client.post("/federation/weights/register", json={
            "model_name": "test-model",
            "shard_index": 0,
            "total_shards": 2,
            "layers": ["layer_1", "layer_2"],
            "node_endpoint": "http://node-a:8087",
        })
        assert r.status_code == 200
        assert "shard_id" in r.json()
        assert r.json()["status"] == "registered"

    def test_register_multiple_shards(self):
        for i in range(3):
            r = client.post("/federation/weights/register", json={
                "model_name": "test-model",
                "shard_index": i,
                "total_shards": 3,
                "layers": [f"layer_{i}"],
                "node_endpoint": f"http://node-{i}:8087",
            })
            assert r.status_code == 200
        manifest = client.get("/federation/weights/manifest").json()
        assert len(manifest["shards"]) == 3
        assert "test-model@v1.0.0" in manifest["topology"]

    def test_register_update_existing(self):
        r1 = client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 0, "total_shards": 1,
            "layers": ["l1"], "node_endpoint": "http://old:8087",
        })
        sid = r1.json()["shard_id"]
        r2 = client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 0, "total_shards": 1,
            "layers": ["l1"], "node_endpoint": "http://new:8087",
        })
        assert r2.json()["status"] == "updated"
        manifest = client.get("/federation/weights/manifest").json()
        shard = [s for s in manifest["shards"] if s["shard_id"] == sid][0]
        assert shard["node_endpoint"] == "http://new:8087"


class TestWeightStorage:
    def test_store_weight_shard(self):
        client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 0, "total_shards": 1,
            "layers": ["l1"], "node_endpoint": "http://n:8087",
        })
        r = client.post("/federation/weights/store", json={
            "shard_id": "m-v1.0.0-shard-0",
            "weights_b64": "W1sxLjAsIDIuMF0sIFszLjAsIDQuMF1d",
            "metadata": {"test": True},
        })
        assert r.status_code == 200
        assert r.json()["status"] == "stored"
        assert "checksum" in r.json()

    def test_shard_info_has_weights_flag(self):
        client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 0, "total_shards": 1,
            "layers": ["l1"], "node_endpoint": "http://n:8087",
        })
        client.post("/federation/weights/store", json={
            "shard_id": "m-v1.0.0-shard-0",
            "weights_b64": "WzFd",
        })
        r = client.get("/federation/weights/shard/m-v1.0.0-shard-0")
        assert r.json()["has_weights"] is True


class TestShardInfo:
    def test_get_shard_info(self):
        client.post("/federation/weights/register", json={
            "model_name": "info-model", "shard_index": 0, "total_shards": 2,
            "layers": ["l1"], "node_endpoint": "http://n:8087",
        })
        r = client.get("/federation/weights/shard/info-model-v1.0.0-shard-0")
        assert r.status_code == 200
        assert r.json()["model_name"] == "info-model"
        assert r.json()["shard_index"] == 0

    def test_get_shard_info_not_found(self):
        r = client.get("/federation/weights/shard/nonexistent")
        assert r.status_code == 404


class TestHealthReport:
    def test_report_health(self):
        client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 0, "total_shards": 1,
            "layers": ["l1"], "node_endpoint": "http://n:8087",
        })
        r = client.post("/federation/weights/health", json={
            "node_endpoint": "http://n:8087",
            "shard_id": "m-v1.0.0-shard-0",
            "healthy": False,
            "load": 0.9,
        })
        assert r.status_code == 200
        assert r.json()["healthy"] is False

    def test_health_not_found(self):
        r = client.post("/federation/weights/health", json={
            "node_endpoint": "http://n:8087",
            "shard_id": "nonexistent",
            "healthy": True,
        })
        assert r.status_code == 404


class TestFederationStatus:
    def test_status_empty(self):
        r = client.get("/federation/weights/status")
        assert r.status_code == 200
        assert r.json()["total_shards"] == 0

    def test_status_with_shards(self):
        client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 0, "total_shards": 2,
            "layers": ["l1"], "node_endpoint": "http://n1:8087",
        })
        client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 1, "total_shards": 2,
            "layers": ["l2"], "node_endpoint": "http://n2:8087",
        })
        r = client.get("/federation/weights/status")
        assert r.json()["total_shards"] == 2
        assert r.json()["healthy_shards"] == 2
        assert r.json()["topologies"] == ["m@v1.0.0"]


class TestInferenceCoordinator:
    def test_inference_missing_topology(self):
        r = client.post("/federation/weights/inference", json={
            "model_name": "nonexistent",
            "input_data": [[1.0, 2.0]],
        })
        assert r.status_code == 404

    def test_inference_not_all_shards_healthy(self):
        client.post("/federation/weights/register", json={
            "model_name": "m", "shard_index": 0, "total_shards": 2,
            "layers": ["l1"], "node_endpoint": "http://n1:8087",
        })
        r = client.post("/federation/weights/inference", json={
            "model_name": "m",
            "input_data": [[1.0, 2.0]],
        })
        assert r.status_code == 503


class TestCLIImports:
    def test_tool_imports(self):
        from tools.federate_weights import cmd_shard, cmd_distribute, cmd_test
        assert callable(cmd_shard)
        assert callable(cmd_distribute)
        assert callable(cmd_test)
