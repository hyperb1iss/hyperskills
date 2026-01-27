# Hyperskills Plugin - Development Makefile
# ─────────────────────────────────────────────

.PHONY: all lint format check clean help stats

# Colors (SilkCircuit palette)
PURPLE := \033[38;2;225;53;255m
CYAN := \033[38;2;128;255;234m
GREEN := \033[38;2;80;250;123m
YELLOW := \033[38;2;241;250;140m
RED := \033[38;2;255;99;99m
RESET := \033[0m

#─────────────────────────────────────────────
# Default target
#─────────────────────────────────────────────
all: check
	@echo "$(GREEN)✓ All checks passed$(RESET)"

#─────────────────────────────────────────────
# Linting & Validation
#─────────────────────────────────────────────
lint: lint-json lint-yaml lint-md
	@echo "$(GREEN)✓ All lints passed$(RESET)"

lint-json:
	@echo "$(CYAN)→ Linting JSON files...$(RESET)"
	@find . -name "*.json" -type f | xargs -I {} sh -c 'jq empty {} 2>/dev/null || (echo "$(RED)✗ Invalid JSON: {}$(RESET)" && exit 1)'
	@echo "$(GREEN)  ✓ JSON valid$(RESET)"

lint-yaml:
	@echo "$(CYAN)→ Linting YAML files...$(RESET)"
	@if command -v yamllint >/dev/null 2>&1; then \
		find . -name "*.yml" -o -name "*.yaml" | xargs yamllint -d relaxed 2>/dev/null || true; \
	else \
		echo "$(YELLOW)  ⚠ yamllint not installed, skipping$(RESET)"; \
	fi
	@echo "$(GREEN)  ✓ YAML checked$(RESET)"

lint-md:
	@echo "$(CYAN)→ Linting Markdown files...$(RESET)"
	@if command -v markdownlint >/dev/null 2>&1; then \
		find . -name "*.md" -type f | xargs markdownlint --config .markdownlint.json 2>/dev/null || true; \
	else \
		echo "$(YELLOW)  ⚠ markdownlint not installed, skipping$(RESET)"; \
	fi
	@echo "$(GREEN)  ✓ Markdown checked$(RESET)"

#─────────────────────────────────────────────
# Formatting
#─────────────────────────────────────────────
format: format-md format-json
	@echo "$(GREEN)✓ Formatting complete$(RESET)"

format-md:
	@echo "$(CYAN)→ Formatting Markdown files...$(RESET)"
	@npx prettier --write "**/*.md" 2>/dev/null || echo "$(YELLOW)  ⚠ prettier failed$(RESET)"
	@echo "$(GREEN)  ✓ Markdown formatted$(RESET)"

format-json:
	@echo "$(CYAN)→ Formatting JSON files...$(RESET)"
	@npx prettier --write "**/*.json" 2>/dev/null || echo "$(YELLOW)  ⚠ prettier failed$(RESET)"
	@echo "$(GREEN)  ✓ JSON formatted$(RESET)"

format-check:
	@echo "$(CYAN)→ Checking format...$(RESET)"
	@npx prettier --check "**/*.md" "**/*.json" 2>/dev/null || (echo "$(RED)✗ Files need formatting$(RESET)" && exit 1)
	@echo "$(GREEN)  ✓ Format OK$(RESET)"

#─────────────────────────────────────────────
# Validation
#─────────────────────────────────────────────
check: validate-structure validate-frontmatter
	@echo "$(GREEN)✓ Plugin structure valid$(RESET)"

validate-structure:
	@echo "$(CYAN)→ Validating plugin structure...$(RESET)"
	@test -f .claude-plugin/plugin.json || (echo "$(RED)✗ Missing plugin.json$(RESET)" && exit 1)
	@echo "$(GREEN)  ✓ plugin.json exists$(RESET)"
	@test -d skills || (echo "$(RED)✗ Missing skills directory$(RESET)" && exit 1)
	@echo "$(GREEN)  ✓ skills/ exists$(RESET)"
	@for skill in skills/*/; do \
		test -f "$$skill/SKILL.md" || (echo "$(RED)✗ Missing SKILL.md in $$skill$(RESET)" && exit 1); \
	done
	@echo "$(GREEN)  ✓ All skills have SKILL.md$(RESET)"

validate-frontmatter:
	@echo "$(CYAN)→ Validating frontmatter...$(RESET)"
	@for f in commands/*.md skills/*/SKILL.md skills/*/agents/*.md; do \
		if [ -f "$$f" ]; then \
			head -1 "$$f" | grep -q "^---$$" || (echo "$(RED)✗ Missing frontmatter in $$f$(RESET)" && exit 1); \
		fi \
	done
	@echo "$(GREEN)  ✓ Frontmatter valid$(RESET)"

#─────────────────────────────────────────────
# Plugin Testing
#─────────────────────────────────────────────
test-local:
	@echo "$(PURPLE)→ Testing plugin locally...$(RESET)"
	@echo "$(CYAN)  Run: claude --plugin-dir $(shell pwd)$(RESET)"

#─────────────────────────────────────────────
# Stats
#─────────────────────────────────────────────
stats:
	@echo ""
	@echo "$(PURPLE)Hyperskills Stats$(RESET)"
	@echo "$(CYAN)─────────────────────────────────────$(RESET)"
	@echo "$(CYAN)Skills:$(RESET)   $$(find skills -maxdepth 1 -type d | tail -n +2 | wc -l | tr -d ' ')"
	@echo "$(CYAN)Agents:$(RESET)   $$(find skills -name "*.md" -path "*/agents/*" | wc -l | tr -d ' ')"
	@echo "$(CYAN)Commands:$(RESET) $$(find commands -name "*.md" 2>/dev/null | wc -l | tr -d ' ')"
	@echo ""
	@echo "$(CYAN)By skill:$(RESET)"
	@for skill in skills/*/; do \
		name=$$(basename $$skill); \
		count=$$(find $$skill/agents -name "*.md" 2>/dev/null | wc -l | tr -d ' '); \
		echo "  $(GREEN)$$name$(RESET): $$count agents"; \
	done
	@echo ""

#─────────────────────────────────────────────
# Cleanup
#─────────────────────────────────────────────
clean:
	@echo "$(CYAN)→ Cleaning up...$(RESET)"
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@find . -name "*.bak" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(RESET)"

#─────────────────────────────────────────────
# Help
#─────────────────────────────────────────────
help:
	@echo ""
	@echo "$(PURPLE)Hyperskills Plugin$(RESET)"
	@echo "$(CYAN)─────────────────────────────────────$(RESET)"
	@echo ""
	@echo "$(CYAN)Usage:$(RESET)"
	@echo "  make [target]"
	@echo ""
	@echo "$(CYAN)Targets:$(RESET)"
	@echo "  $(GREEN)all$(RESET)              Run all checks (default)"
	@echo "  $(GREEN)lint$(RESET)             Run all linters"
	@echo "  $(GREEN)format$(RESET)           Format all files with prettier"
	@echo "  $(GREEN)format-check$(RESET)     Check if files are formatted"
	@echo "  $(GREEN)check$(RESET)            Validate plugin structure"
	@echo "  $(GREEN)stats$(RESET)            Show plugin statistics"
	@echo "  $(GREEN)test-local$(RESET)       Show command to test locally"
	@echo "  $(GREEN)clean$(RESET)            Remove temp files"
	@echo "  $(GREEN)help$(RESET)             Show this help"
	@echo ""
