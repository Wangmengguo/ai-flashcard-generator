#!/usr/bin/env python3
"""
Configuration validation script for AI Flashcard Generator
Validates Docker, environment, and deployment configurations
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

class ConfigValidator:
    """Validates various configuration files and settings"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def log_error(self, message: str):
        self.errors.append(f"❌ ERROR: {message}")
    
    def log_warning(self, message: str):
        self.warnings.append(f"⚠️  WARNING: {message}")
    
    def log_info(self, message: str):
        self.info.append(f"ℹ️  INFO: {message}")
    
    def validate_docker_compose(self) -> bool:
        """Validate docker-compose.yml configuration"""
        compose_file = self.project_root / "docker-compose.yml"
        
        if not compose_file.exists():
            self.log_error("docker-compose.yml not found")
            return False
        
        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_config = yaml.safe_load(f)
            
            # Check version
            if 'version' not in compose_config:
                self.log_warning("No version specified in docker-compose.yml")
            elif compose_config['version'] < '3.8':
                self.log_warning(f"Docker Compose version {compose_config['version']} is older than recommended 3.8+")
            
            # Check services
            if 'services' not in compose_config:
                self.log_error("No services defined in docker-compose.yml")
                return False
            
            services = compose_config['services']
            
            # Check main app service
            if 'flashcard-app' not in services:
                self.log_error("Main application service 'flashcard-app' not found")
            else:
                app_service = services['flashcard-app']
                self._validate_service(app_service, 'flashcard-app')
            
            # Check networks
            if 'networks' in compose_config:
                self.log_info("Networks configuration found")
            
            # Check volumes
            if 'volumes' in compose_config:
                self.log_info("Volumes configuration found")
            
            self.log_info("docker-compose.yml syntax validation passed")
            return True
            
        except yaml.YAMLError as e:
            self.log_error(f"Invalid YAML syntax in docker-compose.yml: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error reading docker-compose.yml: {e}")
            return False
    
    def _validate_service(self, service: Dict[str, Any], service_name: str):
        """Validate individual service configuration"""
        # Check required fields
        required_fields = ['build', 'ports', 'environment']
        missing_fields = [field for field in required_fields if field not in service]
        
        if missing_fields:
            self.log_warning(f"Service '{service_name}' missing recommended fields: {missing_fields}")
        
        # Check port configuration
        if 'ports' in service:
            ports = service['ports']
            if not isinstance(ports, list) or not ports:
                self.log_warning(f"Service '{service_name}' has invalid port configuration")
        
        # Check environment variables
        if 'environment' in service:
            env_vars = service['environment']
            if isinstance(env_vars, list):
                for env_var in env_vars:
                    if 'OPENROUTER_API_KEY' in env_var:
                        self.log_info(f"Service '{service_name}' has OPENROUTER_API_KEY configured")
    
    def validate_dockerfile(self) -> bool:
        """Validate Dockerfile configuration"""
        dockerfile = self.project_root / "Dockerfile"
        
        if not dockerfile.exists():
            self.log_error("Dockerfile not found")
            return False
        
        try:
            with open(dockerfile, 'r', encoding='utf-8') as f:
                dockerfile_content = f.read()
            
            # Check for multi-stage build
            if 'FROM' in dockerfile_content and dockerfile_content.count('FROM') > 1:
                self.log_info("Multi-stage build detected")
            
            # Check for non-root user
            if 'USER' in dockerfile_content:
                self.log_info("Non-root user configuration found")
            else:
                self.log_warning("No USER directive found - container may run as root")
            
            # Check for health check
            if 'HEALTHCHECK' in dockerfile_content:
                self.log_info("Health check configuration found")
            else:
                self.log_warning("No HEALTHCHECK directive found")
            
            # Check for security best practices
            if 'pip install' in dockerfile_content and '--no-cache-dir' in dockerfile_content:
                self.log_info("Pip cache optimization found")
            
            self.log_info("Dockerfile validation passed")
            return True
            
        except Exception as e:
            self.log_error(f"Error reading Dockerfile: {e}")
            return False
    
    def validate_environment_files(self) -> bool:
        """Validate environment configuration files"""
        env_files = [
            ".env.example",
            ".env.development", 
            ".env.production"
        ]
        
        all_valid = True
        
        for env_file in env_files:
            file_path = self.project_root / env_file
            if not file_path.exists():
                self.log_error(f"Environment file {env_file} not found")
                all_valid = False
                continue
            
            if self._validate_env_file(file_path, env_file):
                self.log_info(f"Environment file {env_file} validated")
            else:
                all_valid = False
        
        return all_valid
    
    def _validate_env_file(self, file_path: Path, filename: str) -> bool:
        """Validate individual environment file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_vars = [
                'ENVIRONMENT',
                'PORT',
                'LOG_LEVEL',
                'OPENROUTER_API_KEY',
                'CORS_ORIGINS'
            ]
            
            missing_vars = []
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                self.log_warning(f"{filename} missing variables: {missing_vars}")
            
            # Check for production-specific requirements
            if 'production' in filename:
                prod_vars = ['SECRET_KEY', 'SSL_ENABLED']
                missing_prod_vars = [var for var in prod_vars if var not in content]
                if missing_prod_vars:
                    self.log_warning(f"{filename} missing production variables: {missing_prod_vars}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error reading {filename}: {e}")
            return False
    
    def validate_requirements(self) -> bool:
        """Validate requirements files"""
        req_files = [
            "requirements.txt",
            "requirements.prod.txt", 
            "requirements.dev.txt"
        ]
        
        all_valid = True
        
        for req_file in req_files:
            file_path = self.project_root / req_file
            if not file_path.exists():
                if req_file == "requirements.txt":
                    self.log_error(f"Critical requirements file {req_file} not found")
                    all_valid = False
                else:
                    self.log_warning(f"Optional requirements file {req_file} not found")
                continue
            
            if self._validate_requirements_file(file_path, req_file):
                self.log_info(f"Requirements file {req_file} validated")
            else:
                all_valid = False
        
        return all_valid
    
    def _validate_requirements_file(self, file_path: Path, filename: str) -> bool:
        """Validate individual requirements file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_packages = ['fastapi', 'uvicorn', 'httpx', 'pydantic']
            
            missing_packages = []
            for package in required_packages:
                if package not in content.lower():
                    missing_packages.append(package)
            
            if missing_packages:
                self.log_error(f"{filename} missing critical packages: {missing_packages}")
                return False
            
            # Check for version pinning
            lines = content.strip().split('\n')
            unpinned_packages = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-r'):
                    if '>=' not in line and '==' not in line and '~=' not in line:
                        unpinned_packages.append(line)
            
            if unpinned_packages:
                self.log_warning(f"{filename} has unpinned packages: {unpinned_packages}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error reading {filename}: {e}")
            return False
    
    def validate_logging_config(self) -> bool:
        """Validate logging configuration"""
        logging_file = self.project_root / "logging.json"
        
        if not logging_file.exists():
            self.log_warning("logging.json not found")
            return False
        
        try:
            with open(logging_file, 'r', encoding='utf-8') as f:
                logging_config = json.load(f)
            
            # Check required sections
            required_sections = ['version', 'formatters', 'handlers', 'loggers']
            missing_sections = [section for section in required_sections if section not in logging_config]
            
            if missing_sections:
                self.log_error(f"logging.json missing sections: {missing_sections}")
                return False
            
            # Check for file handlers
            handlers = logging_config.get('handlers', {})
            file_handlers = [name for name, config in handlers.items() 
                           if config.get('class') == 'logging.handlers.RotatingFileHandler']
            
            if file_handlers:
                self.log_info(f"File logging handlers configured: {file_handlers}")
            else:
                self.log_warning("No file logging handlers configured")
            
            self.log_info("logging.json validation passed")
            return True
            
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON syntax in logging.json: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error reading logging.json: {e}")
            return False
    
    def validate_file_structure(self) -> bool:
        """Validate project file structure"""
        required_files = [
            "main.py",
            "index.html",
            "Dockerfile",
            "docker-compose.yml",
            "requirements.txt",
            ".env.example"
        ]
        
        recommended_files = [
            "README.md",
            "DEPLOYMENT_GUIDE.md",
            "DEPLOYMENT_CHECKLIST.md",
            ".dockerignore",
            "Makefile"
        ]
        
        all_valid = True
        
        # Check required files
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                self.log_error(f"Required file {file_name} not found")
                all_valid = False
            else:
                self.log_info(f"Required file {file_name} found")
        
        # Check recommended files
        for file_name in recommended_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                self.log_warning(f"Recommended file {file_name} not found")
            else:
                self.log_info(f"Recommended file {file_name} found")
        
        return all_valid
    
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print("🔍 Starting configuration validation...\n")
        
        validations = [
            ("File Structure", self.validate_file_structure),
            ("Docker Compose", self.validate_docker_compose),
            ("Dockerfile", self.validate_dockerfile),
            ("Environment Files", self.validate_environment_files),
            ("Requirements Files", self.validate_requirements),
            ("Logging Configuration", self.validate_logging_config)
        ]
        
        all_passed = True
        
        for name, validation_func in validations:
            print(f"📋 Validating {name}...")
            try:
                result = validation_func()
                if result:
                    print(f"✅ {name} validation passed")
                else:
                    print(f"❌ {name} validation failed")
                    all_passed = False
            except Exception as e:
                print(f"💥 {name} validation crashed: {e}")
                all_passed = False
            print()
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary"""
        print("=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        if self.errors:
            print(f"\n🚨 ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.info:
            print(f"\nℹ️  INFO ({len(self.info)}):")
            for info in self.info:
                print(f"  {info}")
        
        print("\n" + "=" * 60)
        
        if not self.errors:
            print("🎉 All critical validations passed!")
            print("✅ Configuration is ready for deployment")
        else:
            print("🚨 Critical errors found - please fix before deployment")
        
        if self.warnings:
            print("⚠️  Please review warnings for optimal configuration")

def main():
    """Main validation function"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    validator = ConfigValidator(project_root)
    success = validator.run_all_validations()
    validator.print_summary()
    
    # Exit with error code if validation failed
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()