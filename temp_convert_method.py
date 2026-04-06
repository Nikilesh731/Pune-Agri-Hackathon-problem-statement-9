def _convert_to_result_format(self, processing_result: Dict[str, Any]) -> DocumentProcessingResult:
        """
        Convert processor result to DocumentProcessingResult format
        
        Args:
            processing_result: Raw processor result
        
        Returns:
            DocumentProcessingResult model
        """
        data = processing_result.get("data")
        
        # Add LLM analysis if we have extracted data
        if data and isinstance(data, dict):
            try:
                # Get extracted data for LLM analysis - CRITICAL: Preserve all fields including canonical
                extracted_data = {
                    "document_type": data.get("document_type", "unknown"),
                    "structured_data": data.get("structured_data", {}),
                    "extracted_fields": data.get("extracted_fields", {}),
                    "missing_fields": data.get("missing_fields", []),
                    "confidence": data.get("confidence") or data.get("extraction_confidence") or 0,
                    "reasoning": data.get("reasoning", []),
                    "canonical": data.get("canonical", {}),  # CRITICAL: Preserve canonical field
                    "classification_confidence": data.get("classification_confidence", 0),
                    "classification_reasoning": data.get("classification_reasoning", [])
                }
                
                if extracted_data.get("structured_data") or extracted_data.get("canonical"):
                    # Ensure extraction_confidence is set in final output (this is the field in the Pydantic model)
                    data["extraction_confidence"] = extracted_data["confidence"]

                    # Defensive: initialize intelligence outputs with safe defaults
                    summary = ""
                    case_insight = []
                    decision_support = {"decision": "review", "confidence": 0.5, "reasoning": []}
                    predictions = {}

                    # Generate intelligence outputs independently so one failing piece doesn't cascade
                    try:
                        try:
                            tmp_summary = self.intelligence_service.generate_document_summary(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_document_summary failed: {ie}")
                            tmp_summary = None

                        try:
                            tmp_case_insight = self.intelligence_service.generate_case_insight(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_case_insight failed: {ie}")
                            tmp_case_insight = None

                        try:
                            tmp_decision_support = self.intelligence_service.generate_decision_support(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_decision_support failed: {ie}")
                            tmp_decision_support = None

                        try:
                            tmp_predictions = self.intelligence_service.generate_predictions(extracted_data)
                        except Exception as ie:
                            print(f"DEBUG: generate_predictions failed: {ie}")
                            tmp_predictions = None

                        # Coerce to safe types and apply defaults
                        summary = self._safe_str(tmp_summary)
                        if not summary:
                            # Deterministic officer summary fallback built from extracted facts
                            summary = self._build_officer_summary(extracted_data)

                        case_insight = self._safe_list(tmp_case_insight)
                        decision_support = self._safe_dict(tmp_decision_support)
                        # Ensure decision_support contract
                        decision_support.setdefault("decision", "review")
                        decision_support.setdefault("confidence", 0.5)
                        if not isinstance(decision_support.get("reasoning"), list):
                            decision_support["reasoning"] = self._safe_list(decision_support.get("reasoning"))

                        predictions = self._safe_dict(tmp_predictions)

                        # Attach intelligence outputs to extracted_data and response data
                        extracted_data["summary"] = summary
                        extracted_data["case_insight"] = case_insight
                        extracted_data["decision_support"] = decision_support
                        extracted_data["predictions"] = predictions
                        extracted_data["decision"] = decision_support.get("decision", "review")

                        # Update data dictionary with intelligence outputs
                        data["summary"] = summary
                        data["ai_summary"] = summary
                        data["case_insight"] = case_insight
                        data["decision_support"] = decision_support
                        data["predictions"] = predictions
                        data["decision"] = extracted_data["decision"]

                    except Exception as e:
                        # Defensive catch-all: keep deterministic summary and facts; do not cascade to full failure
                        print(f"DEBUG: Unexpected intelligence processing error: {e}")
                        # Ensure safe minimal outputs
                        summary = summary or self._build_officer_summary(extracted_data)
                        case_insight = case_insight or []
                        decision_support = self._safe_dict(decision_support)
                        decision_support.setdefault("decision", "review")
                        decision_support.setdefault("confidence", 0.5)
                        predictions = predictions or {}

                        extracted_data["summary"] = summary
                        extracted_data["case_insight"] = case_insight
                        extracted_data["decision_support"] = decision_support
                        extracted_data["predictions"] = predictions
                        extracted_data["decision"] = decision_support.get("decision", "review")

                        # Update data dictionary
                        data["summary"] = summary
                        data["ai_summary"] = summary
                        data["case_insight"] = case_insight
                        data["decision_support"] = decision_support
                        data["predictions"] = predictions
                        data["decision"] = extracted_data["decision"]

                    # RANDOM FOREST ML INTEGRATION (separate, defensive)
                    if ML_SERVICE_AVAILABLE:
                        try:
                            ml_analysis = None
                            try:
                                ml_analysis = analyze_document_risk(extracted_data)
                            except Exception as ml_error:
                                print(f"Random Forest ML call failed: {ml_error}")
                                ml_analysis = {}

                            ml_analysis = self._safe_dict(ml_analysis)

                            # Safe nested fields
                            pte = self._safe_dict(ml_analysis.get("processing_time_estimate", {}))
                            priority_score = self._safe_number(ml_analysis.get("priority_score", 50.0), default=50.0)
                            queue = ml_analysis.get("queue") if isinstance(ml_analysis.get("queue"), str) else "NORMAL"
                            risk_level = ml_analysis.get("risk_level") if isinstance(ml_analysis.get("risk_level"), str) else "Medium"
                            processing_time_days = pte.get("estimated_days") if isinstance(pte.get("estimated_days"), (int, float)) else 2
                            approval_likelihood_num = self._safe_number(ml_analysis.get("approval_likelihood", 50), default=50)
                            approval_likelihood = f"{int(round(approval_likelihood_num))}%"
                            model_confidence = self._safe_number(ml_analysis.get("confidence_score", 0.5), default=0.5)
                            auto_decision = ml_analysis.get("auto_decision") if isinstance(ml_analysis.get("auto_decision"), str) else "manual_review"

                            ml_insights = {
                                "priority_score": priority_score,
                                "queue": queue,
                                "risk_level": risk_level,
                                "processing_time": processing_time_days,
                                "approval_likelihood": approval_likelihood,
                                "model_confidence": model_confidence,
                                "auto_decision": auto_decision,
                                "prediction_method": "random_forest"
                            }

                            # If ML signals high risk, add reasoning and escalate if appropriate
                            if str(risk_level).lower() == "high":
                                if not isinstance(decision_support.get("reasoning"), list):
                                    decision_support["reasoning"] = self._safe_list(decision_support.get("reasoning"))
                                decision_support["reasoning"].append("High risk detected by ML model")
                                # Escalate to manual review only if not an explicit approve
                                if decision_support.get("decision") != "approve":
                                    decision_support["decision"] = "manual_review"
                                    extracted_data["decision"] = "manual_review"
                                    data["decision"] = "manual_review"

                            extracted_data["ml_insights"] = ml_insights
                            data["ml_insights"] = ml_insights

                            ml_predictions = {
                                "priority_score": priority_score,
                                "queue": queue,
                                "risk_level": risk_level,
                                "model_confidence": model_confidence,
                                "prediction_method": "random_forest",
                                "processing_time": f"{processing_time_days} days",
                                "approval_likelihood": approval_likelihood
                            }

                            extracted_data["predictions"] = ml_predictions
                            data["predictions"] = ml_predictions

                        except Exception as ml_error:
                            print(f"Random Forest ML error: {ml_error}")
                            # Fall back to deterministic priority computation (does not overwrite intelligence outputs)
                            self._fallback_ml_priority(extracted_data, data, decision_support)
                    else:
                        # No ML service available -> deterministic fallback
                        self._fallback_ml_priority(extracted_data, data, decision_support)
                
                # Apply supporting document sanitization
                if extracted_data.get("document_type") == "supporting_document":
                    extracted_data = self._sanitize_supporting_document(extracted_data)
                    data["structured_data"] = extracted_data.get("structured_data", {})
                    data["extracted_fields"] = extracted_data.get("extracted_fields", {})
                    
                    # Add intelligence data to main data object for final response
                    data["summary"] = summary
                    data["ai_summary"] = summary
                    data["case_insight"] = case_insight
                    data["decision_support"] = decision_support
                    data["predictions"] = predictions
                    data["decision"] = extracted_data.get("decision", "review")

                    # Run LLM analysis defensively
                    try:
                        ai_output = analyze_application(extracted_data)
                    except Exception as ai_err:
                        print(f"DEBUG: analyze_application failed: {ai_err}")
                        ai_output = {}

                    ai_output = self._safe_dict(ai_output)

                    # Add AI analysis to the main data object (not nested under extracted_data)
                    data["ai_summary"] = self._safe_str(ai_output.get("ai_summary", ""))

                    # Merge AI risk flags with existing ones (AI flags come first)
                    ai_risk_flags = self._safe_list(ai_output.get("risk_flags", []))
                    existing_risk_flags = self._safe_list(data.get("risk_flags", []))
                    data["risk_flags"] = ai_risk_flags + existing_risk_flags

                    # FIX 1: SINGLE SOURCE OF TRUTH - Deterministic decision_support ALWAYS takes precedence
                    deterministic_decision_support = self._safe_dict(extracted_data.get("decision_support"))
                    ai_decision_support = self._safe_dict(ai_output.get("decision_support"))

                    if deterministic_decision_support:
                        # Ensure top-level decision matches deterministic decision_support (SINGLE SOURCE OF TRUTH)
                        data["decision"] = deterministic_decision_support.get("decision", "review")
                    elif ai_decision_support:
                        # Only use AI decision_support if deterministic one is absent
                        data["decision_support"] = ai_decision_support
                        # Sync top-level decision with AI decision_support
                        data["decision"] = ai_decision_support.get("decision", "review")
                    
                    # STEP 7: LLM REFINEMENT LAYER - Add advisory block without overriding deterministic truth
                    try:
                        extracted_data_with_refinement = add_llm_refinement_to_response(extracted_data)
                        
                        # Add llm_refinement to main data object
                        data["llm_refinement"] = extracted_data_with_refinement.get("llm_refinement", {})
                            
                    except Exception as e:
                        # LLM refinement failure should not break the pipeline
                        fallback_refinement = {
                            "refined_summary": "LLM refinement temporarily unavailable",
                            "officer_note": "Proceed with deterministic analysis",
                            "consistency_flags": [],
                            "confidence_note": f"LLM refinement failed: {str(e)}"
                        }
                        
                        data["llm_refinement"] = fallback_refinement
            except Exception as e:
                # If LLM analysis fails, keep deterministic outputs and add minimal AI fallbacks
                fallback_decision = "review"
                data["ai_summary"] = "AI analysis temporarily unavailable"
                data["risk_flags"] = [{
                    "code": "AI_ANALYSIS_FAILED",
                    "severity": "medium",
                    "message": f"AI analysis failed: {str(e)}"
                }]
                # Only set decision_support if not already present
                if not data.get("decision_support"):
                    data["decision_support"] = {
                        "decision": fallback_decision,
                        "confidence": 0.5,
                        "reasoning": [f"AI analysis failed: {str(e)}"]
                    }
                # Do not override an existing deterministic decision
                data.setdefault("decision", fallback_decision)
        
        # STRICT VALIDATION: Ensure all required intelligence fields are present
        if data and isinstance(data, dict):
            # Convert to dict for easier validation
            data_dict = data
            
            # AMOUNT VALIDATION: remove unrealistic amounts before final output
            structured_data = data_dict.get("structured_data", {})
            amount_fields = ["requested_amount", "claim_amount", "subsidy_amount", "amount"]
            invalid_amount_removed = False
            for amt_field in amount_fields:
                if amt_field in structured_data and structured_data.get(amt_field) is not None and str(structured_data.get(amt_field)).strip():
                    raw_val = structured_data.get(amt_field)
                    try:
                        # Clean numeric value
                        clean = str(raw_val).replace(",", "").replace("₹", "").replace("$", "").strip()
                        import re
                        clean = re.sub(r"[^0-9.]", "", clean)
                        if clean:
                            amount_num = float(clean)
                            if amount_num > 10000000 or amount_num < 100:
                                # Remove invalid amount from structured_data
                                del structured_data[amt_field]
                                data["structured_data"] = structured_data
                                invalid_amount_removed = True
                    except Exception:
                        # If parsing fails, do not hallucinate or remove
                        pass

            if invalid_amount_removed:
                # Add explicit reasoning about removed invalid amount(s)
                data.setdefault("reasoning", [])
                data["reasoning"].append("Invalid amount removed")

            # DYNAMIC SCORE: compute score from confidence and missing fields
            try:
                doc_type_for_score = data_dict.get("document_type", "unknown")
                required_fields_list = self.extraction_service._compute_missing_fields(doc_type_for_score, {})
                required_count = len(required_fields_list) if required_fields_list is not None else 0
                missing_count = len(data_dict.get("missing_fields", []))
                confidence_val = data_dict.get("confidence", data_dict.get("extraction_confidence", 0.0)) or 0.0
                missing_ratio = missing_count / max(required_count, 1)
                score_val = confidence_val * (1 - missing_ratio)
                # Clamp score between 0 and 1
                score_val = max(0.0, min(1.0, score_val))
                # Persist score
                data["score"] = score_val
            except Exception:
                pass

            # Validate summary is meaningful (not generic)
            summary = data_dict.get("summary")
            if not summary or "temporarily unavailable" in summary or "scheme application regarding scheme application" in summary:
                # Build a minimal, non-hallucinated officer-facing summary using only extracted fields
                document_type = data_dict.get("document_type", "document")
                structured_data = data_dict.get("structured_data", {}) or {}
                name = structured_data.get("farmer_name") or structured_data.get("applicant_name") or structured_data.get("applicant") or "Unknown"

                fixed_summary = f"Applicant {name} submitted a {document_type.replace('_', ' ')} related request."

                # If an amount exists (and wasn't removed), include it
                amt_val = None
                for af in amount_fields:
                    if af in structured_data and structured_data.get(af) is not None and str(structured_data.get(af)).strip():
                        amt_val = structured_data.get(af)
                        break
                if amt_val:
                    # Format numeric amounts cleanly when possible
                    try:
                        clean_amt = str(amt_val).replace(",", "").replace("₹", "").replace("$", "").strip()
                        import re
                        clean_amt_digits = re.sub(r"[^0-9.]", "", clean_amt)
                        if clean_amt_digits:
                            amt_num = float(clean_amt_digits)
                            if amt_num >= 100:
                                if amt_num >= 100000:
                                    formatted = f"₹{int(amt_num):,}"
                                else:
                                    formatted = f"₹{int(amt_num)}"
                                fixed_summary += f" The requested amount is {formatted}."
                            else:
                                fixed_summary += f" The requested amount is {amt_val}."
                        else:
                            fixed_summary += f" The requested amount is {amt_val}."
                    except Exception:
                        fixed_summary += f" The requested amount is {amt_val}."

                # Include a short list of key fields if present
                important_keys = ["scheme_name", "application_id", "aadhaar_number", "village", "location"]
                key_parts = []
                for k in important_keys:
                    if k in structured_data and structured_data.get(k):
                        key_parts.append(f"{k}: {structured_data.get(k)}")
                if key_parts:
                    fixed_summary += f" Key details include {', '.join(key_parts)}."

                data["summary"] = fixed_summary
                data["ai_summary"] = fixed_summary
            
            # Validate decision exists
            decision = data_dict.get("decision")
            if not decision or decision not in ["approve", "review", "reject"]:
                # Auto-fix with conservative decision
                data["decision"] = "review"
            
            # Validate ml_insights exists
            ml_insights = data_dict.get("ml_insights")
            if not ml_insights or not isinstance(ml_insights, dict):
                print(f"DEBUG: ml_insights validation failed, using fallback")
                # Auto-fix with fallback ML insights using real deterministic method
                ml_prediction = predict_application_priority(data_dict)
                fallback_ml = {
                    "priority_score": ml_prediction.get("priority_score", 0.4),
                    "queue": ml_prediction.get("queue", "LOW"),
                    "review_type": ml_prediction.get("review_type", "MANUAL_REVIEW"),
                    "model_confidence": ml_prediction.get("model_confidence", 0.4),
                    "prediction_method": ml_prediction.get("prediction_method", "rule_based_fallback")
                }
                # Add generic predictions for non-ML fields
                fallback_ml.update({
                    "processing_time": "3 days",
                    "approval_likelihood": "50%",
                    "risk_level": "Medium"
                })
                data["ml_insights"] = fallback_ml
                data["predictions"] = fallback_ml  # Also update predictions!
            else:
                print(f"DEBUG: ml_insights validation passed, keeping existing")
                # Ensure predictions field matches ml_insights prediction_method
                data["predictions"] = {
                    "priority_score": ml_insights.get("priority_score", 0.5),
                    "queue": ml_insights.get("queue", "NORMAL"),
                    "review_type": ml_insights.get("review_type", "AUTO"),
                    "model_confidence": ml_insights.get("model_confidence", 0.5),
                    "prediction_method": ml_insights.get("prediction_method", "trained_random_forest")
                }
                # Add generic predictions for non-ML fields
                data["predictions"].update({
                    "processing_time": ml_insights.get("processing_time", "2 days"),
                    "approval_likelihood": ml_insights.get("approval_likelihood", "50%"),
                    "risk_level": ml_insights.get("risk_level", "Medium")
                })
            
            # Validate case_insight has at least 3 useful lines
            case_insight = data_dict.get("case_insight", [])
            if not case_insight or len(case_insight) < 3:
                # Auto-fix with basic case insight
                structured_data = data_dict.get("structured_data", {})
                farmer_name = structured_data.get("farmer_name", "Unknown farmer") if structured_data else "Unknown farmer"
                document_type = data_dict.get("document_type", "document")
                
                fixed_insight = [
                    f"Farmer: {farmer_name}",
                    f"Request: {document_type.replace('_', ' ')}",
                    "Status: Requires review"
                ]
                
                data["case_insight"] = fixed_insight
            
            # WORKFLOW INTEGRATION: Add workflow information
            try:
                workflow_summary = self.workflow_service.get_workflow_summary(data_dict)
                data["workflow"] = workflow_summary["workflow"]
                data["next_steps"] = workflow_summary["next_steps"]
                data["sla_timeline"] = workflow_summary["sla_timeline"]
            except Exception as e:
                print(f"DEBUG: Workflow integration failed: {e}")
                # Add fallback workflow
                fallback_workflow = {
                    "status": "PENDING_REVIEW",
                    "queue": "NORMAL",
                    "estimated_processing_time": "2 days",
                    "requires_manual_review": True,
                    "risk_level": "Medium"
                }
                data["workflow"] = fallback_workflow
                data["next_steps"] = ["Standard processing", "Review required"]
                data["sla_timeline"] = {"initial_review": "3-5 business days", "final_decision": "7-10 business days"}

        return DocumentProcessingResult(
            request_id=processing_result.get("request_id", ""),
            success=processing_result.get("success", False),
            processing_time_ms=processing_result.get("processing_time_ms", 0),
            processing_type=processing_result.get("processing_type", ""),
            filename=processing_result.get("filename", ""),
            data=data,
            metadata=processing_result.get("metadata", {}),
            error_message=processing_result.get("error_message")
        )
