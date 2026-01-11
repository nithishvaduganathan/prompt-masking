"""
Demo script to showcase the Privacy-Preserving AI Chatbot functionality
Run this script to see masking and unmasking in action
"""

from app.masking import mask_prompt, unmask_response


def print_separator():
    """Print a separator line"""
    print("\n" + "=" * 80 + "\n")


def demo_masking():
    """Demonstrate masking functionality with various examples"""
    
    print("🔐 PRIVACY-PRESERVING AI CHATBOT - MASKING DEMO")
    print_separator()
    
    # Example 1: Mental Health
    print("Example 1: Mental Health Condition")
    print("-" * 80)
    text1 = "I'm dealing with depression and anxiety. Can you help me?"
    result1 = mask_prompt(text1)
    print(f"Original:  {result1.original_text}")
    print(f"Masked:    {result1.masked_text}")
    print(f"Protected: {len(result1.detected_entities)} sensitive items")
    for entity in result1.detected_entities:
        print(f"  - {entity}")
    
    print_separator()
    
    # Example 2: Contact Information
    print("Example 2: Contact Information")
    print("-" * 80)
    text2 = "My email is john.doe@example.com and my phone is 555-123-4567"
    result2 = mask_prompt(text2)
    print(f"Original:  {result2.original_text}")
    print(f"Masked:    {result2.masked_text}")
    print(f"Protected: {len(result2.detected_entities)} sensitive items")
    for entity in result2.detected_entities:
        print(f"  - {entity}")
    
    print_separator()
    
    # Example 3: Complex Personal Information
    print("Example 3: Complex Personal Information")
    print("-" * 80)
    text3 = "I'm a 30-year-old female with diabetes living in San Francisco. Email: patient@example.com"
    result3 = mask_prompt(text3)
    print(f"Original:  {result3.original_text}")
    print(f"Masked:    {result3.masked_text}")
    print(f"Protected: {len(result3.detected_entities)} sensitive items")
    for entity in result3.detected_entities:
        print(f"  - {entity}")
    
    print_separator()
    
    # Example 4: Medical Condition
    print("Example 4: Multiple Medical Conditions")
    print("-" * 80)
    text4 = "I have been diagnosed with cancer and also suffer from PTSD"
    result4 = mask_prompt(text4)
    print(f"Original:  {result4.original_text}")
    print(f"Masked:    {result4.masked_text}")
    print(f"Protected: {len(result4.detected_entities)} sensitive items")
    for entity in result4.detected_entities:
        print(f"  - {entity}")
    
    print_separator()
    
    # Example 5: Location-based Query
    print("Example 5: Location-based Information")
    print("-" * 80)
    text5 = "I live in New York and need mental health support. I'm 25 years old."
    result5 = mask_prompt(text5)
    print(f"Original:  {result5.original_text}")
    print(f"Masked:    {result5.masked_text}")
    print(f"Protected: {len(result5.detected_entities)} sensitive items")
    for entity in result5.detected_entities:
        print(f"  - {entity}")
    
    print_separator()
    
    # Example 6: Unmasking
    print("Example 6: Unmasking Demonstration")
    print("-" * 80)
    masked_response = "At [AGE_0], dealing with [MENTAL_HEALTH_0] is common. Contact [EMAIL_0] for support in [LOCATION_0]."
    mappings = {
        "[AGE_0]": "25 years old",
        "[MENTAL_HEALTH_0]": "anxiety",
        "[EMAIL_0]": "support@example.com",
        "[LOCATION_0]": "New York"
    }
    unmasked = unmask_response(masked_response, mappings)
    print(f"Masked Response:   {masked_response}")
    print(f"Unmasked Response: {unmasked}")
    
    print_separator()
    
    print("✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  ✓ Mental health condition masking")
    print("  ✓ Medical condition masking")
    print("  ✓ Email address masking")
    print("  ✓ Phone number masking")
    print("  ✓ Age information masking")
    print("  ✓ Gender information masking")
    print("  ✓ Location masking")
    print("  ✓ Response unmasking")
    print("\n🔒 All sensitive information is protected before being sent to external LLMs!")


if __name__ == "__main__":
    demo_masking()
