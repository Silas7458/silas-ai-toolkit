"""
Wire Discord webhook nodes into n8n workflows.
Adds HTTP Request nodes that post to Discord channels after key events.
"""
import json
import copy

WORKFLOWS_DIR = "{{HOME_DIR}}/amerix-saas/n8n-workflows"

COUNCIL_WEBHOOK = "YOUR_COUNCIL_DECISIONS_WEBHOOK_URL"
ALERTS_WEBHOOK = "YOUR_ALERTS_WEBHOOK_URL"

def make_discord_node(name, webhook_url, message_expr, position):
    """Create an HTTP Request node that posts to a Discord webhook."""
    return {
        "parameters": {
            "method": "POST",
            "url": webhook_url,
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Content-Type", "value": "application/json"}
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": message_expr,
            "options": {
                "timeout": 10000
            }
        },
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": position
    }


def add_node_after(wf, source_node_name, new_node, source_output=0):
    """Add a new node and connect it after the source node."""
    # Add node to nodes array
    wf["nodes"].append(new_node)

    # Add connection from source to new node
    if source_node_name not in wf["connections"]:
        wf["connections"][source_node_name] = {"main": [[]]}

    main = wf["connections"][source_node_name]["main"]

    # Ensure enough output slots exist
    while len(main) <= source_output:
        main.append([])

    main[source_output].append({
        "node": new_node["name"],
        "type": "main",
        "index": 0
    })


def get_node_position(wf, node_name):
    """Get position of an existing node."""
    for n in wf["nodes"]:
        if n["name"] == node_name:
            return n["position"]
    return [0, 0]


def wire_deliberation_pipeline():
    """Add Discord post to #council-decisions after Insert Decision."""
    path = f"{WORKFLOWS_DIR}/COUNCIL-Deliberation-Pipeline--08WM371MryB61MGT.json"
    with open(path, encoding="utf-8") as f:
        wf = json.load(f)

    # Check if already wired
    if any(n["name"].startswith("Discord:") for n in wf["nodes"]):
        print("  SKIP: Discord node already exists")
        return

    pos = get_node_position(wf, "Insert Decision")
    msg_expr = json.dumps({
        "content": "={{ \"**[Council Engine]** Decision logged\\n\" + \"**Topic:** \" + ($json.topic || \"N/A\") + \"\\n\" + \"**Confidence:** \" + ($json.confidence || \"N/A\") + \"\\n\" + \"**Decision:** \" + (($json.decision || \"\").substring(0, 500)) + (($json.decision || \"\").length > 500 ? \"...\" : \"\") }}"
    })

    node = make_discord_node(
        "Discord: Post Decision",
        COUNCIL_WEBHOOK,
        msg_expr,
        [pos[0] + 300, pos[1]]
    )

    add_node_after(wf, "Insert Decision", node)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("  OK: Added 'Discord: Post Decision' after 'Insert Decision'")


def wire_error_handler():
    """Add Discord alert to #alerts after Mark Session Failed."""
    path = f"{WORKFLOWS_DIR}/COUNCIL-Error-Handler--hD0Kh4mxu8cLoOwl.json"
    with open(path, encoding="utf-8") as f:
        wf = json.load(f)

    if any(n["name"].startswith("Discord:") for n in wf["nodes"]):
        print("  SKIP: Discord node already exists")
        return

    pos = get_node_position(wf, "Mark Session Failed")
    msg_expr = json.dumps({
        "content": "={{ \"**[Council Engine]** :warning: Deliberation FAILED\\n\" + \"**Session:** \" + ($json.session_id || \"unknown\") + \"\\n\" + \"**Error:** \" + ($json.error || $json.message || \"unknown error\") + \"\\n\" + \"**Status:** Abandoned after max retries\" }}"
    })

    node = make_discord_node(
        "Discord: Alert Failure",
        ALERTS_WEBHOOK,
        msg_expr,
        [pos[0] + 300, pos[1]]
    )

    add_node_after(wf, "Mark Session Failed", node)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("  OK: Added 'Discord: Alert Failure' after 'Mark Session Failed'")


def wire_heartbeat_monitor():
    """Add Discord alert to #alerts after Notify Agents."""
    path = f"{WORKFLOWS_DIR}/COUNCIL-Heartbeat-Monitor--z4yzjnt39FQJID0S.json"
    with open(path, encoding="utf-8") as f:
        wf = json.load(f)

    if any(n["name"].startswith("Discord:") for n in wf["nodes"]):
        print("  SKIP: Discord node already exists")
        return

    pos = get_node_position(wf, "Notify Agents")
    msg_expr = json.dumps({
        "content": "={{ \"**[Heartbeat Monitor]** :rotating_light: Infrastructure alert\\n\" + ($json.failures_summary || $json.message || \"Health check failures detected — check notification queues\") }}"
    })

    node = make_discord_node(
        "Discord: Alert Heartbeat",
        ALERTS_WEBHOOK,
        msg_expr,
        [pos[0] + 300, pos[1]]
    )

    add_node_after(wf, "Notify Agents", node)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("  OK: Added 'Discord: Alert Heartbeat' after 'Notify Agents'")


def wire_daily_health_check():
    """Add Discord alert to #alerts after Notify Sister."""
    path = f"{WORKFLOWS_DIR}/Daily-Health-Check--cNRy2M4RaAL6usIo.json"
    with open(path, encoding="utf-8") as f:
        wf = json.load(f)

    if any(n["name"].startswith("Discord:") for n in wf["nodes"]):
        print("  SKIP: Discord node already exists")
        return

    pos = get_node_position(wf, "Notify Sister")
    msg_expr = json.dumps({
        "content": "={{ \"**[Daily Health Check]** :warning: Issues detected\\n\" + \"**Issues:** \" + ($json.issues || \"unknown\") + \"\\n\" + ($json.report || \"Check health-report.md for details\").substring(0, 800) }}"
    })

    node = make_discord_node(
        "Discord: Alert Health",
        ALERTS_WEBHOOK,
        msg_expr,
        [pos[0] + 300, pos[1]]
    )

    add_node_after(wf, "Notify Sister", node)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("  OK: Added 'Discord: Alert Health' after 'Notify Sister'")


if __name__ == "__main__":
    print("Wiring Discord webhooks into n8n workflows...\n")

    print("1. [COUNCIL] Deliberation Pipeline -> #council-decisions")
    wire_deliberation_pipeline()

    print("\n2. [COUNCIL] Error Handler -> #alerts")
    wire_error_handler()

    print("\n3. [COUNCIL] Heartbeat Monitor -> #alerts")
    wire_heartbeat_monitor()

    print("\n4. Daily Health Check -> #alerts")
    wire_daily_health_check()

    print("\nDone. Import updated workflows via: n8n import:workflow --input=<file>")
