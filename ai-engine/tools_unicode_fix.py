#!/usr/bin/env python3
"""
Unicode Input Sanitizer for OpenAI Agent SDK
Fixes the issue where tools disappear when copy-pasted content contains problematic Unicode characters.

Based on research from OpenAI Community reports about tool availability issues with Unicode.
"""

import re
import unicodedata
from typing import Dict, Any

class UnicodeInputSanitizer:
    """
    Sanitizes input to prevent OpenAI Agent SDK from losing tools due to Unicode issues.
    
    This addresses the known issue where copy-pasted content with hidden Unicode 
    characters causes tools to become unavailable in the Agent SDK.
    """
    
    def __init__(self):
        # Characters that commonly cause tool availability issues
        self.problematic_patterns = [
            # Unicode escape sequences that aren't properly handled
            r'\\u[0-9a-fA-F]{4}',
            r'\\x[0-9a-fA-F]{2}',
            # Null bytes and control characters
            r'\x00',
            r'[\x01-\x08\x0E-\x1F\x7F]',  # Control characters except \t, \n, \r
            # Zero-width characters
            r'[\u200B-\u200D\uFEFF]',
            # Curly quotes (common from copy-paste)
            r'[\u201C\u201D\u2018\u2019]',
            # Other problematic Unicode ranges reported in issues
            r'[\u0000\u000C\u000A]'
        ]
        
        # Replacement mappings for common problematic characters
        self.replacements = {
            '\u201C': '"',  # Left double quotation mark
            '\u201D': '"',  # Right double quotation mark  
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u00A0': ' ',  # Non-breaking space
            '\u200B': '',   # Zero-width space
            '\u200C': '',   # Zero-width non-joiner
            '\u200D': '',   # Zero-width joiner
            '\uFEFF': '',   # Zero-width no-break space (BOM)
        }
    
    def detect_issues(self, text: str) -> Dict[str, Any]:
        """
        Detect potential Unicode issues that could cause tool availability problems.
        
        Returns:
            Dict with 'has_issues', 'issues_found', and 'problematic_chars'
        """
        issues = []
        problematic_chars = set()
        
        # Check for problematic patterns
        for pattern in self.problematic_patterns:
            matches = re.findall(pattern, text)
            if matches:
                issues.append(f"Found pattern: {pattern}")
                problematic_chars.update(matches)
        
        # Check for non-ASCII characters
        for i, char in enumerate(text):
            if ord(char) > 127:  # Non-ASCII
                if char not in self.replacements:
                    issues.append(f"Non-ASCII character at position {i}: {repr(char)} (U+{ord(char):04X})")
                    problematic_chars.add(char)
        
        # Check for mixed encodings (common copy-paste issue)
        try:
            text.encode('ascii')
        except UnicodeEncodeError as e:
            issues.append(f"ASCII encoding error: {str(e)}")
        
        return {
            'has_issues': len(issues) > 0,
            'issues_found': issues,
            'problematic_chars': list(problematic_chars)
        }
    
    def sanitize_for_agent_sdk(self, text: str) -> str:
        """
        Sanitize text to prevent OpenAI Agent SDK tool availability issues.
        
        This is the main method to fix the copy-paste Unicode problem.
        """
        if not text:
            return text
        
        # Step 1: Apply known character replacements
        sanitized = text
        for problematic, replacement in self.replacements.items():
            sanitized = sanitized.replace(problematic, replacement)
        
        # Step 2: Remove or replace problematic patterns
        for pattern in self.problematic_patterns:
            # Remove null bytes and control characters
            if 'x00' in pattern or 'x01-x08' in pattern:
                sanitized = re.sub(pattern, '', sanitized)
            # Remove zero-width characters
            elif '200B-200D' in pattern:
                sanitized = re.sub(pattern, '', sanitized)
            # Handle Unicode escape sequences
            elif '\\u[0-9a-fA-F]{4}' == pattern:
                # Convert \uXXXX to actual Unicode characters
                def replace_unicode_escape(match):
                    try:
                        code_point = int(match.group(0)[2:], 16)
                        return chr(code_point)
                    except (ValueError, OverflowError):
                        return ''  # Remove invalid sequences
                sanitized = re.sub(pattern, replace_unicode_escape, sanitized)
        
        # Step 3: Normalize Unicode (NFC normalization)
        sanitized = unicodedata.normalize('NFC', sanitized)
        
        # Step 4: Final cleanup - remove any remaining problematic characters
        # Keep only printable characters plus common whitespace
        sanitized = ''.join(char for char in sanitized 
                          if char.isprintable() or char in '\n\r\t')
        
        return sanitized
    
    def safe_agent_input(self, user_input: str) -> str:
        """
        Main public method: safely prepare input for OpenAI Agent SDK.
        
        This prevents the "tools disappearing" issue when copy-pasting content.
        """
        detection = self.detect_issues(user_input)
        
        if detection['has_issues']:
            print(f"🛠️ Detected {len(detection['issues_found'])} Unicode issues that could cause tools to disappear.")
            print("   Sanitizing input to preserve tool availability...")
            
            sanitized = self.sanitize_for_agent_sdk(user_input)
            
            # Verify the fix worked
            post_detection = self.detect_issues(sanitized)
            if not post_detection['has_issues']:
                print("✅ Input sanitized successfully. Tools should remain available.")
            else:
                print(f"⚠️ Warning: {len(post_detection['issues_found'])} issues remain after sanitization.")
            
            return sanitized
        else:
            return user_input


# Utility functions for easy integration
def fix_copy_paste_input(text: str) -> str:
    """
    Quick fix for copy-pasted text that causes tools to disappear.
    
    Usage:
        user_input = fix_copy_paste_input(user_input)
        result = await Runner.run(agent, user_input)
    """
    sanitizer = UnicodeInputSanitizer()
    return sanitizer.safe_agent_input(text)


def detect_tool_breaking_chars(text: str) -> Dict[str, Any]:
    """
    Detect characters that might cause OpenAI Agent SDK tools to become unavailable.
    
    Returns detailed information about problematic characters found.
    """
    sanitizer = UnicodeInputSanitizer()
    return sanitizer.detect_issues(text)


# Example usage and testing
if __name__ == "__main__":
    # Test cases based on real issues reported
    test_cases = [
        "Normal text should work fine",
        "Text with \u201ccurly quotes\u201d from copy-paste",
        "Text with zero-width spaces\u200Bhidden\u200Ccharacters",
        "Mixed encoding: café résumé naïve",
        "Control characters: \x00\x01\x02",
        "Unicode escapes: \\u201C\\u201D",
        "Korean text that breaks tools: 떡볶이",
        "HTML-formatted copy-paste: &quot;hello&quot; &amp; goodbye"
    ]
    
    sanitizer = UnicodeInputSanitizer()
    
    print("🧪 Testing Unicode Input Sanitizer\n")
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"Test {i}: {repr(test_input[:50])}")
        
        detection = sanitizer.detect_issues(test_input)
        if detection['has_issues']:
            print(f"  ❌ Issues found: {len(detection['issues_found'])}")
            sanitized = sanitizer.sanitize_for_agent_sdk(test_input)
            print(f"  ✅ Sanitized: {repr(sanitized[:50])}")
            
            # Verify fix
            post_check = sanitizer.detect_issues(sanitized)
            print(f"  🔍 After fix: {'✅ Clean' if not post_check['has_issues'] else '⚠️ Issues remain'}")
        else:
            print("  ✅ No issues detected")
        print() 