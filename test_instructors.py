#!/usr/bin/env python3
import json

# Load test data
with open('data/tedu_cmpe_courses_metadata.json', 'r') as f:
    courses = json.load(f)

# Find CMPE 113
course = [c for c in courses if c['code'] == 'CMPE 113'][0]

print("Original data:")
print(f"  instructor: {course.get('instructor')}")
print(f"  instructors: {course.get('instructors')}")

# Apply the same logic as the script
instructors = []
if course.get('instructor'):
    instructors.append(course['instructor'])
if course.get('instructors'):
    for inst_list in course['instructors']:
        if isinstance(inst_list, str):
            instructors.extend([i.strip() for i in inst_list.split(',')])
        else:
            instructors.append(str(inst_list))

# Remove duplicates
unique_instructors = list(dict.fromkeys([i for i in instructors if i]))
instructor_str = ', '.join(unique_instructors) if unique_instructors else None

print(f"\nProcessed result:")
print(f"  Final instructor string: {instructor_str}")
print(f"  Instructors list: {unique_instructors}")
