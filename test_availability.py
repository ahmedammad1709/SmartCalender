import requests
import json
from datetime import datetime, timedelta

# Test the availability system
base_url = "http://localhost:5000"

def test_agenda_availability():
    """Test agenda availability endpoint"""
    print("Testing agenda availability...")
    
    # Test with an existing agenda ID (from the database we saw)
    agenda_id = 2  # Ammad agenda
    
    response = requests.get(f"{base_url}/agenda/{agenda_id}/availability")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Agenda availability loaded successfully")
        print(f"   Title: {data['title']}")
        print(f"   Duration: {data['duration']} minutes")
        print(f"   Availability: {json.dumps(data['availability'], indent=2)}")
        return True
    else:
        print(f"❌ Failed to load agenda availability: {response.status_code}")
        print(response.text)
        return False

def test_available_slots():
    """Test available slots for different days"""
    print("\nTesting available slots...")
    
    agenda_id = 2  # Ammad agenda
    today = datetime.now()
    
    # Test different days of the week
    days_to_test = [
        (today + timedelta(days=0)).strftime('%Y-%m-%d'),  # Today
        (today + timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
        (today + timedelta(days=2)).strftime('%Y-%m-%d'),  # Day after tomorrow
        (today + timedelta(days=7)).strftime('%Y-%m-%d'),  # Next week
    ]
    
    for date in days_to_test:
        response = requests.get(f"{base_url}/agenda/{agenda_id}/slots/{date}")
        
        if response.status_code == 200:
            data = response.json()
            day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
            print(f"\n📅 {day_name} ({date}):")
            
            if data['available']:
                print(f"   ✅ Available slots: {len(data['slots'])}")
                if data['slots']:
                    print(f"   First slot: {data['slots'][0]['display']}")
                    print(f"   Last slot: {data['slots'][-1]['display']}")
            else:
                print(f"   ❌ {data['message']}")
        else:
            print(f"❌ Failed to get slots for {date}: {response.status_code}")

def test_agenda_with_limited_availability():
    """Test agenda with limited availability (like the Web Dev agenda)"""
    print("\nTesting agenda with limited availability...")
    
    agenda_id = 11  # Web Dev agenda (only Tuesday 9:00-13:00)
    
    # Test Tuesday
    today = datetime.now()
    # Find next Tuesday
    days_ahead = (1 - today.weekday()) % 7  # 1 = Tuesday
    if days_ahead == 0:
        days_ahead = 7
    next_tuesday = today + timedelta(days=days_ahead)
    tuesday_date = next_tuesday.strftime('%Y-%m-%d')
    
    response = requests.get(f"{base_url}/agenda/{agenda_id}/slots/{tuesday_date}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📅 Tuesday ({tuesday_date}):")
        
        if data['available']:
            print(f"   ✅ Available slots: {len(data['slots'])}")
            if data['slots']:
                print(f"   Time range: {data['slots'][0]['display']} - {data['slots'][-1]['display']}")
        else:
            print(f"   ❌ {data['message']}")
    
    # Test Wednesday (should not be available)
    next_wednesday = next_tuesday + timedelta(days=1)
    wednesday_date = next_wednesday.strftime('%Y-%m-%d')
    
    response = requests.get(f"{base_url}/agenda/{agenda_id}/slots/{wednesday_date}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📅 Wednesday ({wednesday_date}):")
        
        if data['available']:
            print(f"   ❌ Should not be available but got slots")
        else:
            print(f"   ✅ Correctly shows no availability: {data['message']}")

if __name__ == "__main__":
    print("🧪 Testing SmartCal Availability System")
    print("=" * 50)
    
    try:
        test_agenda_availability()
        test_available_slots()
        test_agenda_with_limited_availability()
        print("\n✅ All tests completed!")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error during testing: {e}") 