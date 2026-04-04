import re

test_str = 'Rs. 2,60,000'
clean_amount = test_str.strip()
clean_amount = re.sub(r'\b(rs\.?|inr|rupee|rupees|₹)\b', '', clean_amount, flags=re.IGNORECASE)
clean_amount = re.sub(r'^\.\s*', '', clean_amount)
print(f'After cleanup: "{clean_amount}"')

# Test the new patterns
pattern1 = r'(\d{1,3}(?:,\d{2})+(?:,\d{3})*)'
match1 = re.search(pattern1, clean_amount)
print(f'Pattern 1: {match1.group(1) if match1 else "No match"}')

pattern2 = r'(\d{1,3}(?:,\d{3})*\d{3})'
match2 = re.search(pattern2, clean_amount)
print(f'Pattern 2: {match2.group(1) if match2 else "No match"}')

pattern3 = r'(\d{1,3},\d{3})'
match3 = re.search(pattern3, clean_amount)
print(f'Pattern 3: {match3.group(1) if match3 else "No match"}')

# Test longest match logic
all_matches = []
for pattern in [pattern1, pattern2, pattern3]:
    match = re.search(pattern, clean_amount)
    if match:
        all_matches.append(match.group(1))

print(f'All matches: {all_matches}')
if all_matches:
    longest_match = max(all_matches, key=len)
    print(f'Longest match: {longest_match} -> {longest_match.replace(",", "")}')
