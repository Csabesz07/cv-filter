"""
Create a test ranking to generate audit events with bias detection.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Login credentials (adjust as needed)
LOGIN_DATA = {
    "username": "admin",
    "password": "admin123"
}

def login():
    """Login and get auth token."""
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=LOGIN_DATA)
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"✅ Logged in successfully. Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def get_organization_id(token):
    """Get organization ID."""
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{BASE_URL}/api/organizations/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            org_id = data[0]["id"]
            org_name = data[0]["name"]
            print(f"✅ Organization: {org_name} (ID: {org_id})")
            return org_id
    
    print("❌ Failed to get organization")
    return None

def get_role_id(token, org_id):
    """Get or create a test role."""
    headers = {"Authorization": f"Token {token}"}
    
    # Try to get existing roles
    response = requests.get(
        f"{BASE_URL}/api/roles/",
        headers=headers,
        params={"organization": org_id}
    )
    
    if response.status_code == 200:
        roles = response.json()
        if roles and len(roles) > 0:
            role_id = roles[0]["id"]
            role_title = roles[0]["title"]
            print(f"✅ Using role: {role_title} (ID: {role_id})")
            return role_id
    
    # Create a test role if none exists
    role_data = {
        "organization": org_id,
        "title": "Senior Backend Developer",
        "description": "Python/Django developer with 5+ years experience",
        "requirements": {
            "skills": ["Python", "Django", "PostgreSQL", "Docker"],
            "min_experience_years": 5,
            "education_level": "Bachelor"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/roles/",
        headers=headers,
        json=role_data
    )
    
    if response.status_code == 201:
        role_id = response.json()["id"]
        print(f"✅ Created test role (ID: {role_id})")
        return role_id
    
    print("❌ Failed to create role")
    return None

def create_test_ranking(token, org_id, role_id):
    """Create a test ranking run."""
    headers = {"Authorization": f"Token {token}"}
    
    ranking_data = {
        "organization": org_id,
        "role": role_id,
        "criteria": {
            "skills": {
                "weight": 0.4,
                "required": ["Python", "Django"]
            },
            "experience": {
                "weight": 0.35,
                "min_years": 3
            },
            "education": {
                "weight": 0.25,
                "min_level": "Bachelor"
            }
        },
        "max_candidates": 20
    }
    
    print("\n🚀 Starting ranking run...")
    response = requests.post(
        f"{BASE_URL}/api/ranking/runs/",
        headers=headers,
        json=ranking_data
    )
    
    if response.status_code == 201:
        run_data = response.json()
        run_id = run_data["id"]
        print(f"✅ Ranking run created (ID: {run_id})")
        print(f"   Status: {run_data.get('status')}")
        print(f"   Candidates: {run_data.get('candidates_count', 0)}")
        
        if "results" in run_data:
            print(f"\n📊 Results:")
            for result in run_data["results"][:5]:
                print(f"   - {result.get('candidate_name')}: {result.get('score'):.2f}")
        
        return run_id
    else:
        print(f"❌ Failed to create ranking: {response.status_code}")
        print(response.text)
        return None

def check_audit_events(token):
    """Check audit events for bias detection."""
    headers = {"Authorization": f"Token {token}"}
    
    print("\n🔍 Checking audit events...")
    response = requests.get(
        f"{BASE_URL}/api/audit/ranking/",
        headers=headers,
        params={"limit": 10}
    )
    
    if response.status_code == 200:
        events = response.json()
        if isinstance(events, dict):
            events = events.get("results", [])
        
        print(f"✅ Found {len(events)} audit events")
        
        bias_events = [e for e in events if "bias" in e.get("event_type", "")]
        if bias_events:
            print(f"\n⚠️  Bias Detection Events: {len(bias_events)}")
            for event in bias_events:
                print(f"\n   Event: {event['event_type']}")
                print(f"   Time: {event['timestamp']}")
                
                metadata = event.get("metadata", {})
                alerts = metadata.get("bias_indicators", [])
                print(f"   Alerts: {len(alerts)}")
                for alert in alerts:
                    print(f"     - [{alert['severity']}] {alert['type']}: {alert['message']}")
        else:
            print("   No bias events detected")
        
        print(f"\n📋 Recent events:")
        for event in events[:5]:
            print(f"   - {event['event_type']} @ {event['timestamp']}")
    else:
        print(f"❌ Failed to get audit events: {response.status_code}")

if __name__ == "__main__":
    print("=" * 80)
    print("TEST RANKING WITH AUDIT & BIAS DETECTION")
    print("=" * 80)
    
    token = login()
    if not token:
        exit(1)
    
    org_id = get_organization_id(token)
    if not org_id:
        exit(1)
    
    role_id = get_role_id(token, org_id)
    if not role_id:
        exit(1)
    
    run_id = create_test_ranking(token, org_id, role_id)
    
    # Check audit events
    check_audit_events(token)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED!")
    print("=" * 80)
    print("\n💡 Now visit: http://localhost:5173/audit")
    print("   to see the Audit Dashboard with bias detection results!")
