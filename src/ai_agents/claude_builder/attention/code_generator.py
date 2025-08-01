"""
Code Generator - Claude's code generation capabilities
"""

from typing import Dict, Any, Optional, List, Callable
import ast
import json
from pathlib import Path
from datetime import datetime

class CodeGenerator:
    """Handles all code generation tasks for Claude Builder"""
    
    def __init__(self, claude_interface: Callable[[str], str]) -> None:
        self.claude = claude_interface
        self.templates: Dict[str, str] = {}
        self.generation_history: List[Dict[str, Any]] = []
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 
            'cpp', 'go', 'rust', 'html', 'css', 'sql'
        ]
        
    def generate_code(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on specification"""
        language = specification.get('language', 'python')
        task_type = specification.get('type', 'function')
        requirements = specification.get('requirements', [])
        constraints = specification.get('constraints', [])
        
        prompt = self._build_generation_prompt(
            language, task_type, requirements, constraints
        )
        
        code = self.claude(prompt)
        
        # Validate generated code
        validation_result = self._validate_code(code, language)
        
        result = {
            'code': code,
            'language': language,
            'type': task_type,
            'valid': validation_result['valid'],
            'validation_errors': validation_result.get('errors', []),
            'timestamp': datetime.now().isoformat()
        }
        
        self.generation_history.append(result)
        return result
    
    def generate_class(self, class_spec: Dict[str, Any]) -> str:
        """Generate a complete class implementation"""
        prompt = f"""Generate a {class_spec.get('language', 'Python')} class with:
        
        Class Name: {class_spec.get('name', 'MyClass')}
        Purpose: {class_spec.get('purpose', 'General purpose class')}
        
        Properties:
        {json.dumps(class_spec.get('properties', {}), indent=2)}
        
        Methods:
        {json.dumps(class_spec.get('methods', []), indent=2)}
        
        Special Requirements:
        {json.dumps(class_spec.get('requirements', []), indent=2)}
        
        Generate clean, well-documented code with proper error handling."""
        
        result: str = self.claude(prompt)
        return result
    
    def generate_api_endpoint(self, endpoint_spec: Dict[str, Any]) -> str:
        """Generate API endpoint implementation"""
        prompt = f"""Generate an API endpoint with:
        
        Framework: {endpoint_spec.get('framework', 'Flask')}
        Method: {endpoint_spec.get('method', 'GET')}
        Path: {endpoint_spec.get('path', '/api/resource')}
        
        Input Parameters:
        {json.dumps(endpoint_spec.get('parameters', {}), indent=2)}
        
        Business Logic:
        {endpoint_spec.get('logic', 'Process request and return response')}
        
        Response Format:
        {json.dumps(endpoint_spec.get('response_format', {}), indent=2)}
        
        Include proper validation, error handling, and documentation."""
        
        result: str = self.claude(prompt)
        return result
    
    def generate_test_cases(self, code: str, language: str = 'python') -> str:
        """Generate test cases for given code"""
        prompt = f"""Generate comprehensive test cases for this {language} code:
        
        ```{language}
        {code}
        ```
        
        Include:
        - Unit tests for all functions/methods
        - Edge case testing
        - Error condition testing
        - Integration tests if applicable
        - Performance tests for critical sections
        
        Use appropriate testing framework for {language}."""
        
        result: str = self.claude(prompt)
        return result
    
    def refactor_code(self, code: str, improvements: List[str]) -> str:
        """Refactor code based on specified improvements"""
        prompt = f"""Refactor this code with the following improvements:
        
        Original Code:
        ```
        {code}
        ```
        
        Required Improvements:
        {chr(10).join(f'- {imp}' for imp in improvements)}
        
        Maintain functionality while improving:
        - Code clarity and readability
        - Performance
        - Error handling
        - Documentation
        - Design patterns usage"""
        
        result: str = self.claude(prompt)
        return result
    
    def _build_generation_prompt(self, language: str, task_type: str, 
                               requirements: List[str], constraints: List[str]) -> str:
        """Build detailed prompt for code generation"""
        prompt = f"""As Claude the Builder, generate {language} code for a {task_type}.
        
        Requirements:
        {chr(10).join(f'- {req}' for req in requirements)}
        
        Constraints:
        {chr(10).join(f'- {con}' for con in constraints)}
        
        Guidelines:
        - Write clean, efficient, and well-documented code
        - Follow {language} best practices and idioms
        - Include error handling and edge cases
        - Add helpful comments for complex logic
        - Ensure the code is production-ready
        
        Generate the code:"""
        
        return prompt
    
    def _validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """Validate generated code syntax"""
        if language.lower() == 'python':
            try:
                ast.parse(code)
                return {'valid': True}
            except SyntaxError as e:
                return {
                    'valid': False,
                    'errors': [f"Syntax error at line {e.lineno}: {e.msg}"]
                }
        else:
            # For other languages, we'll rely on the AI's generation quality
            return {'valid': True, 'note': f'Syntax validation not implemented for {language}'}
    
    def generate_documentation(self, code: str, doc_type: str = 'api') -> str:
        """Generate documentation for code"""
        prompt = f"""Generate {doc_type} documentation for this code:
        
        ```
        {code}
        ```
        
        Include:
        - Overview and purpose
        - Detailed parameter descriptions
        - Return value documentation
        - Usage examples
        - Error handling information
        - Performance considerations
        
        Format: Markdown with proper sections"""
        
        result: str = self.claude(prompt)
        return result
    
    def generate_design_pattern(self, pattern_name: str, context: Dict[str, Any]) -> str:
        """Generate code using specific design pattern"""
        prompt = f"""Implement the {pattern_name} design pattern for:
        
        Context: {context.get('description', 'General implementation')}
        Components: {json.dumps(context.get('components', []), indent=2)}
        Requirements: {json.dumps(context.get('requirements', []), indent=2)}
        
        Provide:
        - Complete implementation
        - Usage example
        - Explanation of benefits
        - When to use this pattern"""
        
        result: str = self.claude(prompt)
        return result