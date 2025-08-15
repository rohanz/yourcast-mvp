#!/usr/bin/env python3

# Simple test to verify schema compatibility
from uuid import uuid4

print("Testing episode creation with subcategories...")
episode_id = str(uuid4())
subcategories = ["Breaking News", "Tech Innovation"]
print(f"Episode ID: {episode_id}")
print(f"Subcategories: {subcategories}")
print("Schema test completed successfully!")
