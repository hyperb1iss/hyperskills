.PHONY: validate lint format check all

# Validate skill structure
validate:
	@echo "Validating skill structure..."
	@for skill in skills/*/; do \
		if [ ! -f "$$skill/SKILL.md" ]; then \
			echo "ERROR: $$skill missing SKILL.md"; \
			exit 1; \
		fi; \
		echo "✓ $$skill"; \
	done
	@echo "All skills validated!"

# Check frontmatter in all markdown files
check-frontmatter:
	@echo "Checking frontmatter..."
	@find skills commands -name "*.md" | while read file; do \
		if ! head -1 "$$file" | grep -q "^---$$"; then \
			echo "WARNING: $$file missing frontmatter"; \
		fi; \
	done
	@echo "Frontmatter check complete!"

# Lint markdown files
lint:
	@echo "Linting markdown..."
	@npx markdownlint-cli2 "**/*.md" || true

# Format markdown files
format:
	@echo "Formatting..."
	@npx prettier --write "**/*.md" "**/*.json" || true

# Validate JSON files
check-json:
	@echo "Validating JSON..."
	@for file in .claude-plugin/*.json; do \
		jq empty "$$file" && echo "✓ $$file" || exit 1; \
	done

# Run all checks
check: validate check-frontmatter check-json
	@echo ""
	@echo "All checks passed!"

# Full validation and format
all: check format lint
	@echo ""
	@echo "Ready to ship!"

# Count agents and skills
stats:
	@echo "Hyperskills Stats"
	@echo "================="
	@echo "Skills: $$(ls -d skills/*/ 2>/dev/null | wc -l | tr -d ' ')"
	@echo "Agents: $$(find skills -name "*.md" -path "*/agents/*" | wc -l | tr -d ' ')"
	@echo "Commands: $$(ls commands/*.md 2>/dev/null | wc -l | tr -d ' ')"
	@echo ""
	@echo "By skill:"
	@for skill in skills/*/; do \
		name=$$(basename $$skill); \
		count=$$(ls $$skill/agents/*.md 2>/dev/null | wc -l | tr -d ' '); \
		echo "  $$name: $$count agents"; \
	done
