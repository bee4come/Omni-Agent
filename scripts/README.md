# MNEE Nexus Scripts Directory

This directory contains utility scripts for managing and validating the MNEE Nexus system.

## Available Scripts

### `validate_config.py`

**Purpose:** Pre-flight configuration validation

**Description:**
Validates all configuration files and environment variables before system startup. Checks directory structure, YAML configs, dependencies, and contract files.

**Usage:**
```bash
python scripts/validate_config.py
```

**Checks Performed:**
- ✅ Directory structure completeness
- ✅ Environment variable configuration (`.env`)
- ✅ YAML configuration syntax (`agents.yaml`, `services.yaml`)
- ✅ Required dependencies (`requirements.txt`, `package.json`)
- ✅ Smart contract files existence
- ✅ Deployment script availability

**Exit Codes:**
- `0` - All checks passed
- `1` - Critical errors found

**Output Example:**
```
====================================
  MNEE Nexus Configuration Validation
====================================

ℹ️  Checking directory structure...
✅ Directory exists: backend
✅ Directory exists: contracts
...

ℹ️  Checking environment configuration...
✅ Required variable set: ETH_RPC_URL
⚠️  Optional variable not set: OPENAI_API_KEY

====================================
  Validation Summary
====================================
✅ All checks passed! ✓
```

---

## Adding New Scripts

When adding new scripts to this directory:

1. **Naming Convention:** Use snake_case (e.g., `check_health.py`, `backup_data.sh`)
2. **Shebang:** Include appropriate shebang line (`#!/usr/bin/env python3` or `#!/bin/bash`)
3. **Documentation:** Add docstring at the top explaining purpose and usage
4. **Permissions:** Set execute permissions (`chmod +x script_name`)
5. **Error Handling:** Include proper error handling and exit codes
6. **Help Text:** Provide help/usage information
7. **Update README:** Add entry to this README

---

## Future Scripts (Planned)

### High Priority:
- `backup_config.sh` - Backup configuration files
- `restore_config.sh` - Restore configuration from backup
- `check_health.py` - Comprehensive health check for all services
- `migrate_db.py` - Database migration utility

### Medium Priority:
- `generate_report.py` - Generate system usage reports
- `cleanup_logs.sh` - Archive and clean old log files
- `update_providers.sh` - Update provider service configurations
- `test_integration.py` - Run integration tests

### Low Priority:
- `benchmark.py` - Performance benchmarking
- `analyze_logs.py` - Log file analysis and insights
- `export_data.py` - Export transaction data
- `security_audit.sh` - Basic security checks

---

## Script Development Guidelines

### Python Scripts

**Template:**
```python
#!/usr/bin/env python3
"""
Script Name: script_name.py

Description:
Brief description of what the script does

Usage:
    python scripts/script_name.py [options]

Options:
    -h, --help     Show this help message
    -v, --verbose  Verbose output

Author: Your Name
Date: YYYY-MM-DD
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Your code here
    
    return 0  # Success

if __name__ == "__main__":
    sys.exit(main())
```

### Bash Scripts

**Template:**
```bash
#!/bin/bash

##############################################################################
# Script Name: script_name.sh
#
# Description:
#   Brief description of what the script does
#
# Usage:
#   ./scripts/script_name.sh [options]
#
# Options:
#   -h, --help     Show this help message
#   -v, --verbose  Verbose output
#
# Author: Your Name
# Date: YYYY-MM-DD
##############################################################################

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Main logic
main() {
    # Your code here
    print_success "Script completed successfully"
    return 0
}

main "$@"
```

---

## Testing Scripts

Before committing new scripts:

1. **Syntax Check:**
   ```bash
   # Python
   python -m py_compile scripts/your_script.py
   
   # Bash
   bash -n scripts/your_script.sh
   ```

2. **Run Script:**
   ```bash
   # Test with various inputs
   python scripts/your_script.py
   ```

3. **Check Exit Codes:**
   ```bash
   python scripts/your_script.py
   echo $?  # Should be 0 for success
   ```

4. **Test Error Handling:**
   - Test with missing files
   - Test with invalid inputs
   - Test with insufficient permissions

---

## Script Dependencies

### Python Scripts
- Python 3.10+
- PyYAML (for YAML parsing)
- Pathlib (built-in)

### Bash Scripts
- bash 4.0+
- curl (for health checks)
- jq (for JSON parsing, optional)

---

## Contributing

When contributing scripts:

1. Follow the naming conventions above
2. Include comprehensive documentation
3. Add error handling
4. Test thoroughly
5. Update this README
6. Submit PR with description

---

## Support

For issues or questions about scripts:
- Check script documentation first
- Review error messages carefully
- Consult main project README
- Open an issue on GitHub

---

## License

All scripts in this directory are part of the MNEE Nexus project and are licensed under the MIT License.
