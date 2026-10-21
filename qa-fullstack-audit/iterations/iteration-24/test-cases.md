# ITERATION 24 TEST CASES

| Test ID | Requirement | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| `TC-REM-005` | Câu mở đầu đoạn chat Bạch Tuột AI PPTQ | "Xin chào bạn! Mình là Bạch Tuột, trợ lí AI của hệ thống PPTQ. Mình có thể giúp được gì cho bạn?" | Đã hiển thị chính xác từng ký tự (greeting_match=True). | **PASS** |
| `TC-REM-006` | Câu trả lời khi câu hỏi không liên quan / ngoài phạm vi | "Cảm ơn câu hỏi của bạn. Nhưng hiện tại nó đang nằm ngoài phạm vi hiểu biết của mình, mình sẽ ghi nhận câu hỏi này và cải thiện bản thân nhiều hơn để có thể hỗ trợ bạn được nhiều hơn nha" | Đã phản hồi chính xác 100% từng ký tự (refusal_match=True). | **PASS** |
| `TC-REM-007` | Câu trả lời khi câu hỏi xúc phạm, chê bai AI | "Xin lỗi vì đã làm bạn tức giận, không biết mình có thể làm gì để bạn cảm thấy tốt hơn nhỉ?" | Đã phản hồi chính xác 100% từng ký tự (apology_match=True). | **PASS** |
| `TC-REM-008` | Câu chào chuẩn trên trang AI Assistant toàn trang | "Xin chào bạn! Mình là Bạch Tuột, trợ lí AI của hệ thống PPTQ. Mình có thể giúp được gì cho bạn?" | Đã hiển thị chuẩn mực trên trang '#/student/ai-assistant' (page_greeting_match=True). | **PASS** |
