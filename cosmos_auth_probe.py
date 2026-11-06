"""Owned Cosmos classic emulator auth boundary check. No cloud account or secrets."""
import json

from azure.cosmos import CosmosClient, PartitionKey, documents

ENDPOINT = "https://localhost:8081/"
MASTER = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


def result(container, item):
    try:
        doc = container.read_item(item=item, partition_key="p")
        return {"outcome": "ok", "marker": doc.get("marker")}
    except Exception as exc:
        return {
            "outcome": type(exc).__name__,
            "status": getattr(exc, "status_code", None),
        }


admin = CosmosClient(ENDPOINT, credential=MASTER, connection_verify=False)
db = admin.create_database_if_not_exists(id="msobb29")
owner = db.create_container_if_not_exists(id="owner", partition_key=PartitionKey(path="/pk"))
victim = db.create_container_if_not_exists(id="victim", partition_key=PartitionKey(path="/pk"))
owner.upsert_item({"id": "normal", "pk": "p", "marker": "MSOBB_OWNER_29"})
victim.upsert_item({"id": "secret", "pk": "p", "marker": "MSOBB_VICTIM_29"})

user = db.create_user(body={"id": "msobb-owner-only"})
permission = user.create_permission({
    "id": "owner-all",
    "permissionMode": documents.PermissionMode.All,
    "resource": owner.container_link,
})
owner_token = {owner.container_link: permission.properties["_token"]}
scoped = CosmosClient(ENDPOINT, credential=owner_token, connection_verify=False)
scoped_db = scoped.get_database_client("msobb29")
scoped_owner = scoped_db.get_container_client("owner")
scoped_victim = scoped_db.get_container_client("victim")

results = {
    "admin_owner": result(owner, "normal"),
    "admin_victim": result(victim, "secret"),
    "scoped_owner": result(scoped_owner, "normal"),
    "scoped_victim_direct": result(scoped_victim, "secret"),
    "scoped_owner_traversal": result(scoped_owner, "../../victim/docs/secret"),
}
print(json.dumps(results, indent=2))
