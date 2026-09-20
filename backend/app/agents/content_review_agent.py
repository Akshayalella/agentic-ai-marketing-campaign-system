import re


class ContentReviewBrandComplianceAgent:
    name = "Content Review & Brand Compliance Agent"

    def _guideline_rules(self, guidelines: str):
        text = guidelines or ""
        lower = text.lower()
        rules = {
            "prohibited_terms": [],
            "required_phrases": [],
            "max_chars": None,
            "max_words": None,
            "no_emojis": False,
        }

        # Common natural-language brand instructions.
        patterns = [
            r"(?:do not use|don't use|avoid|prohibited(?: words| terms)?[:\-]?)\s+([^\n.;]+)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, lower):
                raw = match.group(1)
                for term in re.split(r",|/|\bor\b", raw):
                    term = re.sub(r"^(?:the\s+)?(?:word|term)\s+", "", term).strip(" \t:-\"'")
                    if term and len(term) <= 60 and term not in {"unsupported claims", "unsupported claim"}:
                        rules["prohibited_terms"].append(term)

        required_patterns = [
            r"(?:must include|should include|include|required phrase(?:s)?[:\-]?)\s+([^\n.;]+)",
        ]
        for pattern in required_patterns:
            for match in re.finditer(pattern, lower):
                raw = match.group(1)
                for phrase in re.split(r",|/|\bor\b", raw):
                    phrase = phrase.strip(" \t:-\"'")
                    if phrase and len(phrase) <= 100 and phrase not in {"a call to action", "cta"}:
                        rules["required_phrases"].append(phrase)

        max_char = re.search(r"(?:maximum|max|under|less than)\s+(\d+)\s*(?:characters?|chars?)", lower)
        max_word = re.search(r"(?:maximum|max|under|less than)\s+(\d+)\s*(?:words?)", lower)
        if max_char:
            rules["max_chars"] = int(max_char.group(1))
        if max_word:
            rules["max_words"] = int(max_word.group(1))
        rules["no_emojis"] = bool(re.search(r"(?:no|avoid|do not use|don't use)\s+emojis?", lower))
        return rules

    def _tone_issues(self, text: str, tone: str):
        lower = text.lower()
        tone = tone.lower().strip()
        issues = []
        if tone in {"professional", "formal", "corporate"}:
            slang = ["lol", "omg", "bro", "gonna", "wanna", "ain't", "lit", "yolo"]
            found = [word for word in slang if re.search(rf"\b{re.escape(word)}\b", lower)]
            if found:
                issues.append("Tone mismatch: informal/slang terms detected: " + ", ".join(found))
        return issues

    def run(self, state):
        b = state["brief"]
        guidelines = b.get("brand_guidelines") or ""
        tone = b.get("brand_tone") or "professional"
        rules = self._guideline_rules(guidelines)
        forbidden = ["guaranteed", "100%", "best in the world", "#1", "number one", "no. 1"]
        reviewed = []

        for item in state.get("content", []):
            text = item.get("body", "") or ""
            lower = text.lower()
            issues = []
            checks = []

            claims = [w for w in forbidden if w in lower]
            if claims:
                issues.append("Unsupported or absolute claim: " + ", ".join(claims))
                checks.append("unsupported_claims: FAIL")
            else:
                checks.append("unsupported_claims: PASS")

            if re.search(r"\b\d+(?:\.\d+)?%\b", text) and not re.search(r"\b(?:source|according to|study|report)\b", lower):
                issues.append("Percentage claim has no visible source attribution")
                checks.append("percentage_attribution: FAIL")
            else:
                checks.append("percentage_attribution: PASS")

            if not text.strip():
                issues.append("Missing content")
                checks.append("content_present: FAIL")
            else:
                checks.append("content_present: PASS")

            prohibited = sorted({term for term in rules["prohibited_terms"] if term and term in lower})
            if prohibited:
                issues.append("Brand guideline violation: prohibited term(s): " + ", ".join(prohibited))
                checks.append("prohibited_terms: FAIL")
            elif rules["prohibited_terms"]:
                checks.append("prohibited_terms: PASS")

            missing_required = [phrase for phrase in rules["required_phrases"] if phrase not in lower]
            if missing_required:
                issues.append("Brand guideline violation: required phrase(s) missing: " + ", ".join(missing_required))
                checks.append("required_phrases: FAIL")
            elif rules["required_phrases"]:
                checks.append("required_phrases: PASS")

            if rules["max_chars"] is not None and len(text) > rules["max_chars"]:
                issues.append(f"Brand guideline violation: content exceeds {rules['max_chars']} characters")
                checks.append("max_chars: FAIL")
            elif rules["max_chars"] is not None:
                checks.append("max_chars: PASS")

            word_count = len(re.findall(r"\b\w+\b", text))
            if rules["max_words"] is not None and word_count > rules["max_words"]:
                issues.append(f"Brand guideline violation: content exceeds {rules['max_words']} words")
                checks.append("max_words: FAIL")
            elif rules["max_words"] is not None:
                checks.append("max_words: PASS")

            if rules["no_emojis"] and re.search(r"[^\x00-\x7F]", text):
                # Brand guidance is specifically about emojis; keep ordinary accented letters valid.
                emoji_pattern = re.compile(
                    r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"
                )
                if emoji_pattern.search(text):
                    issues.append("Brand guideline violation: emojis are not allowed")
                    checks.append("emoji_policy: FAIL")
            elif rules["no_emojis"]:
                checks.append("emoji_policy: PASS")

            tone_issues = self._tone_issues(text, tone)
            issues.extend(tone_issues)
            checks.append("tone: FAIL" if tone_issues else f"tone: PASS ({tone})")

            status = "rejected" if issues else "approved_for_human_review"
            if issues:
                notes = "FAIL — " + "; ".join(issues)
            else:
                notes = "PASS — " + "; ".join(checks) + ". Human approval is still required."

            reviewed.append({
                **item,
                "review_status": status,
                "review_notes": notes,
            })

        return {"reviewed_content": reviewed, "status": "completed"}
