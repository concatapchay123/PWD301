"""Builder for Chapter 5: Kiểm Thử Xâm Nhập & Khai Thác Lỗ Hổng Bảo Mật API GraphQL.
Source book: BlackHat GraphQL.pdf (12 lessons).
Strictly validates >= 600 words for each.
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.build_cyber_payload import generate_lesson_markdown
from scripts.course_data.common import count_vietnamese_words, validate_lesson_data

CHAPTER_5_INFO = {
    "title": "Chương 5: Kiểm Thử Xâm Nhập & Khai Thác Lỗ Hổng Bảo Mật API GraphQL",
    "source_file": "BlackHat GraphQL.pdf",
    "position": 5,
}


def get_chapter_5_lessons() -> list[dict]:
    lessons = []

    configs = [
        (
            1,
            "Bài 5.1: Nhập Môn GraphQL: Kiến Trúc Giao Tiếp, Schema, Resolvers & Khác Biệt Với REST API",
            "Nghiên cứu bản chất kỹ thuật của GraphQL: Ngôn ngữ truy vấn dữ liệu linh hoạt của Facebook/Meta, cơ chế hoạt động của Schema Definition Language (SDL) và phân tích so sánh với kiến trúc REST API.",
            "https://www.youtube.com/watch?v=jyjGneKJynk",
            [
                "Nắm vững nguồn gốc ra đời và lý do GraphQL thay thế REST API trong các ứng dụng hiện đại.",
                "Giải mã các thành phần cốt lõi: Schema, Type System, Resolvers, và Query Parser.",
                "Phân tích sự khác biệt căn bản về bề mặt tấn công giữa REST API và GraphQL API."
            ],
            [
                (
                    "Sự Ra Đời & Triết Lý Cốt Lõi Của GraphQL",
                    "Được phát triển nội bộ bởi Facebook vào năm 2012 và công bố mã nguồn mở năm 2015, GraphQL (Graph Query Language) được thiết kế để giải quyết hai vấn đề nhức nhối kinh điển của REST API: 1. Over-fetching (Tải thừa dữ liệu): Trong REST, khi máy khách chỉ cần tên người dùng, API trả về toàn bộ 50 trường dữ liệu (bao gồm địa chỉ, số điện thoại, lịch sử mua hàng...). 2. Under-fetching (Tải thiếu dữ liệu): Để hiển thị một trang hồ sơ người dùng kèm danh sách bài viết và bình luận, máy khách phải gửi tới 3 hoặc 4 request HTTP liên tiếp (`/users/1`, `/users/1/posts`, `/posts/1/comments`). GraphQL giải quyết triệt để điều này bằng cách trao toàn bộ quyền kiểm soát dữ liệu cho máy khách: Máy khách chỉ cần gửi MỘT truy vấn duy nhất và chỉ định chính xác các trường dữ liệu mình mong muốn."
                ),
                (
                    "Kiến Trúc Giao Tiếp: Một Endpoint Duy Nhất (Single Endpoint)",
                    "Trong khi kiến trúc REST API phân tán tài nguyên qua hàng chục hoặc hàng trăm endpoint đường dẫn HTTP khác nhau (`/api/v1/users`, `/api/v1/orders`) với các phương thức `GET`, `POST`, `PUT`, `DELETE`, GraphQL chỉ sử dụng DUY NHẤT một endpoint tập trung (thường là `POST /graphql` hoặc `POST /api/graphql`). Toàn bộ các thao tác đọc, ghi, cập nhật, xóa đều được bọc trong phần thân (body) của một yêu cầu HTTP POST duy nhất dưới dạng JSON."
                ),
                (
                    "Hệ Thống Kiểu (Type System) & Hàm Phân Giải (Resolvers)",
                    "Trái tim của một GraphQL server gồm hai thành phần: 1. Schema: Bản hợp đồng định nghĩa toàn bộ cấu trúc dữ liệu, các kiểu đối tượng (Object Types), trường (Fields), kiểu dữ liệu cơ bản (Scalars: Int, Float, String, Boolean, ID) bằng ngôn ngữ Schema Definition Language (SDL). 2. Resolver Functions: Các hàm thực thi phía máy chủ chịu trách nhiệm tìm nạp dữ liệu thực tế cho từng trường từ cơ sở dữ liệu (PostgreSQL, MongoDB) hoặc các vi dịch vụ (Microservices) phía sau."
                )
            ],
            "Khác biệt về bề mặt tấn công: Trong REST API, hệ thống phòng thủ có thể đặt tường lửa WAF kiểm tra đường dẫn URL và phương thức HTTP. Trong GraphQL, do tất cả lưu lượng đều đi qua một endpoint duy nhất `POST /graphql` và trả về mã HTTP 200 OK ngay cả khi có lỗi logic bên trong, các WAF truyền thống hoàn toàn bị mù (Blind) và không thể phân biệt giữa truy vấn bình thường và các cuộc tấn công khai thác dữ liệu tinh vi.",
            "Thực hành gửi truy vấn GraphQL đầu tiên bằng công cụ dòng lệnh cURL:",
            ("bash", """# Gửi một truy vấn GraphQL đơn giản tới endpoint công khai
curl -X POST https://countries.trevorblades.com/graphql \\
     -H "Content-Type: application/json" \\
     -d '{"query": "{ countries(filter: { code: { eq: \\"VN\\" } }) { name capital currency emoji } }"}' \\
     | jq ."""),
            ["Không nhầm lẫn rằng mã HTTP 200 của GraphQL là thành công tuyệt đối; luôn kiểm tra trường 'errors' trong gói tin JSON phản hồi.", "Nhận diện việc chuyển sang GraphQL sẽ làm thay đổi toàn bộ chiến lược giám sát an ninh mạng."],
            ["GraphQL trao quyền kiểm soát dữ liệu cho client, loại bỏ over-fetching và under-fetching.", "Toàn bộ giao tiếp của GraphQL diễn ra qua một endpoint duy nhất (thường là POST /graphql).", "WAF truyền thống gặp khó khăn lớn trong việc phân tích các truy vấn lồng nhau của GraphQL."],
            [
                {"question": "GraphQL được phát triển ban đầu bởi tập đoàn công nghệ nào?", "type": "MULTIPLE_CHOICE", "options": ["Google", "Facebook (Meta)", "Microsoft", "Amazon"], "correct_index": 1, "explanation": "Facebook (Meta) phát minh năm 2012."},
                {"question": "Khác với REST API có nhiều URL, GraphQL thường sử dụng mấy endpoint HTTP duy nhất?", "type": "MULTIPLE_CHOICE", "options": ["Chỉ duy nhất 1 endpoint", "10 endpoint", "Tùy theo số bảng database", "Không dùng HTTP"], "correct_index": 0, "explanation": "GraphQL chỉ dùng 1 endpoint duy nhất (ví dụ /graphql)."},
                {"question": "Hiện tượng một endpoint API trả về quá nhiều trường dữ liệu không cần thiết cho client gọi là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Over-fetching", "over-fetching", "overfetching"]}], "explanation": "Over-fetching."}
            ]
        ),
        (
            2,
            "Bài 5.2: Thiết Lập Phòng Lab Thực Hành: Kali Linux, Altair Client & Máy Chủ DVGA",
            "Xây dựng phòng thí nghiệm kiểm thử thâm nhập GraphQL: Triển khai ứng dụng dễ bị tổn thương Damn Vulnerable GraphQL Application (DVGA) trên Docker và làm chủ client Altair.",
            "https://www.youtube.com/watch?v=viWzbPuGqpo",
            [
                "Nắm vững quy trình thiết lập môi trường lab an toàn phục vụ nghiên cứu bảo mật GraphQL.",
                "Triển khai ứng dụng thực hành chuẩn quốc tế DVGA (Damn Vulnerable GraphQL Application) bằng Docker.",
                "Sử dụng thành thạo các công cụ đồ họa: Altair GraphQL Client và GraphQL Playground."
            ],
            [
                (
                    "Tầm Quan Trọng Của Môi Trường Lab Riêng Biệt",
                    "Kiểm thử bảo mật GraphQL bao gồm các kỹ thuật có khả năng làm sập máy chủ ngay lập tức (như Circular Denial of Service, Batching Attacks) hoặc trích xuất toàn bộ cơ sở dữ liệu. Việc thực hiện các hành động này trên các hệ thống sản xuất thực tế mà chưa được cấp phép là vi phạm pháp luật nghiêm trọng. Do đó, việc sở hữu một phòng thí nghiệm cục bộ cô lập, mô phỏng đầy đủ các lỗi bảo mật phổ biến nhất theo chuẩn OWASP là bước chuẩn bị bắt buộc."
                ),
                (
                    "Triển Khai DVGA (Damn Vulnerable GraphQL Application)",
                    "DVGA do hãng bảo mật Doyensec phát triển là ứng dụng chuẩn mực số 1 thế giới để học tập bảo mật GraphQL. Được viết bằng Python/Flask và GraphQL-core, DVGA chứa đầy đủ các kịch bản lỗ hổng từ cơ bản đến nâng cao: Introspection abuse, SQL Injection, NoSQL Injection, Broken Object-Level Authorization, Circular Queries, và File Upload vulnerabilities. Cách triển khai an toàn và nhanh chóng nhất là sử dụng Docker container."
                ),
                (
                    "Làm Chủ Trình Khách Altair GraphQL Client",
                    "Mặc dù cURL rất hữu ích cho tự động hóa, trong giai đoạn phân tích thủ công ban đầu, các chuyên gia pentest sử dụng **Altair GraphQL Client** (ứng dụng desktop hoặc tiện ích mở rộng trình duyệt). Altair cung cấp: Tự động hoàn thành cú pháp truy vấn (Autocomplete); Trình khám phá tài liệu Schema (Docs Explorer); Khả năng thêm các tiêu đề xác thực HTTP Headers (như `Authorization: Bearer <token>`); Và định dạng kết quả JSON trực quan đẹp mắt."
                )
            ],
            "Kịch bản phòng lab: Phân Tích Lỗi Cấu Hình Môi Trường Dev Trên Production: Rất nhiều lập trình viên khi đưa ứng dụng lên production đã quên tắt giao diện đồ họa GraphiQL / Playground (`/graphiql`). Giao diện này cung cấp một bàn điều khiển tương tác trực tiếp cho phép kẻ tấn công thử nghiệm các truy vấn mà không cần cài đặt thêm bất kỳ công cụ nào.",
            "Thực hành cài đặt và khởi chạy máy chủ DVGA bằng Docker trên Kali Linux:",
            ("bash", """# 1. Tải mã nguồn DVGA từ kho lưu trữ GitHub chính thức
git clone https://github.com/doyensec/DVGA.git /tmp/DVGA
cd /tmp/DVGA

# 2. Xây dựng và khởi chạy container Docker của DVGA
docker build -t dvga .
docker run -d -p 5013:5013 --name dvga_server dvga

# 3. Kiểm tra trạng thái máy chủ DVGA đang hoạt động
curl -s http://127.0.0.1:5013/ | grep -i "Damn Vulnerable GraphQL Application"
echo "[+] Phòng lab DVGA đã sẵn sàng tại địa chỉ: http://127.0.0.1:5013/graphql" """),
            ["Luôn đảm bảo container DVGA chỉ mở cổng trên mạng nội bộ localhost (127.0.0.1) để tránh bị bên ngoài khai thác.", "Tắt container khi không sử dụng để tiết kiệm tài nguyên máy tính."],
            ["DVGA là môi trường chuẩn quốc tế để thực hành khai thác các lỗ hổng GraphQL.", "Altair GraphQL Client cung cấp môi trường gửi truy vấn trực quan và khám phá Schema.", "Lỗi để lộ GraphiQL / Playground trên môi trường production là một phát hiện an ninh nghiêm trọng."],
            [
                {"question": "Ứng dụng mã nguồn mở nào do Doyensec phát triển thường được dùng làm môi trường lab bảo mật GraphQL?", "type": "MULTIPLE_CHOICE", "options": ["DVWA", "WebGoat", "DVGA (Damn Vulnerable GraphQL Application)", "Metasploitable"], "correct_index": 2, "explanation": "DVGA (Damn Vulnerable GraphQL Application)."},
                {"question": "Công cụ giao diện đồ họa nào sau đây được sử dụng phổ biến để gửi truy vấn và khám phá Schema GraphQL?", "type": "MULTIPLE_CHOICE", "options": ["Altair", "Wireshark", "John the Ripper", "Hydra"], "correct_index": 0, "explanation": "Altair GraphQL Client."},
                {"question": "Để lộ giao diện GraphiQL tương tác trực tiếp trên môi trường production là một cấu hình an toàn?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. GraphiQL trên production giúp tin tặc dễ dàng thăm dò và khai thác hệ thống."}
            ]
        ),
        (
            3,
            "Bài 5.3: Bộ Công Cụ Tấn Công GraphQL Thiết Yếu: InQL, Graphw00f, Clairvoyance & CrackQL",
            "Trang bị kho vũ khí tấn công GraphQL: Tiện ích mở rộng Burp Suite InQL, máy quét nhận dạng engine Graphw00f, công cụ phục hồi Schema Clairvoyance và công cụ vét cạn CrackQL.",
            "https://www.youtube.com/watch?v=jyjGneKJynk",
            [
                "Nắm vững chức năng và kịch bản sử dụng của từng công cụ trong kho vũ khí Black Hat GraphQL.",
                "Sử dụng InQL (Burp Suite Extension) để tự động sinh toàn bộ danh mục Queries và Mutations.",
                "Thực hành nhận dạng công nghệ máy chủ (Fingerprinting) bằng công cụ Graphw00f."
            ],
            [
                (
                    "Bộ Vũ Khí Tấn Công Chuyên Dụng Cho GraphQL",
                    "Để kiểm thử thâm nhập GraphQL một cách chuyên nghiệp, việc chỉ dựa vào trình duyệt hoặc cURL là không đủ. Các chuyên gia an ninh trên thế giới đã phát triển một hệ sinh thái các công cụ tự động hóa xuất sắc: 1. **InQL (Doyensec)**: Tiện ích mở rộng hàng đầu cho Burp Suite, tự động bóc tách Schema từ truy vấn Introspection và sinh ra toàn bộ danh sách các mẫu Queries, Mutations và Subscriptions có sẵn tham số để sẵn sàng đưa vào Burp Repeater hoặc Scanner. 2. **Graphw00f**: Công cụ trinh sát nhận diện vân tay (Fingerprinting) máy chủ GraphQL. Nó gửi các truy vấn dị dạng để xác định chính xác backend đang chạy engine gì (Apollo, Yoga, GraphQL-Ruby, Hasura, Graphene...). 3. **Clairvoyance**: Công cụ tái tạo lại Schema ngay cả khi tính năng Introspection đã bị quản trị viên tắt hoàn toàn bằng kỹ thuật khai thác gợi ý sửa lỗi (Field Suggestion). 4. **CrackQL**: Công cụ vét cạn mật khẩu và mã OTP siêu tốc tận dụng tính năng Aliasing của GraphQL."
                ),
                (
                    "Cơ Chế Hoạt Động Của InQL Extension",
                    "Khi bạn duyệt web qua Burp Suite Proxy, InQL sẽ tự động phát hiện các yêu cầu GraphQL. Chỉ với một cú nhấp chuột 'Send to InQL', công cụ sẽ: Thực hiện truy vấn Introspection; Phân tích cú pháp cây Schema JSON; Tạo ra một cấu trúc thư mục gồm các tệp truy vấn sẵn sàng kiểm thử: `queries.txt`, `mutations.txt`, `subscriptions.txt`. Giúp tiết kiệm hàng giờ đồng hồ viết cú pháp thủ công."
                ),
                (
                    "Sức Mạnh Của Nhận Dạng Engine Bằng Graphw00f",
                    "Mỗi GraphQL engine có cách xử lý lỗi và cấu trúc thông điệp JSON phản hồi khác nhau. Biết được engine chính xác giúp bạn chọn đúng kỹ thuật khai thác: Ví dụ Apollo Server thường có cơ chế gợi ý lỗi rất chi tiết; Hasura thường kết nối trực tiếp với PostgreSQL; Graphene thường chạy trên Python/Django."
                )
            ],
            "Kịch bản thực chiến: Trinh Sát Nhanh Hệ Thống Mục Tiêu: Chuyên gia pentest chạy Graphw00f vào endpoint của mục tiêu. Trong 2 giây, Graphw00f xác định máy chủ chạy Apollo Server 3.x với tính năng Introspection bị tắt nhưng Field Suggestion vẫn bật, mở đường cho việc phục hồi Schema bằng Clairvoyance.",
            "Thực hành cài đặt và chạy công cụ nhận dạng vân tay Graphw00f trên môi trường dòng lệnh:",
            ("bash", """# 1. Cài đặt công cụ Graphw00f từ GitHub
git clone https://github.com/doyensec/graphw00f.git /tmp/graphw00f
cd /tmp/graphw00f
python3 -m pip install -r requirements.txt

# 2. Quét nhận dạng vân tay engine GraphQL của máy chủ DVGA
python3 main.py -t http://127.0.0.1:5013/graphql -d"""),
            ["Luôn cập nhật các công cụ InQL và Graphw00f lên phiên bản mới nhất để nhận dạng các engine mới.", "Cẩn thận khi sử dụng CrackQL với tần suất quá cao vì có thể làm nghẽn máy chủ mục tiêu."],
            ["InQL tự động hóa việc trích xuất và sinh mẫu truy vấn trong Burp Suite.", "Graphw00f nhận diện chính xác công nghệ engine GraphQL đang chạy phía sau.", "Clairvoyance có khả năng phục hồi Schema khi Introspection đã bị tắt."],
            [
                {"question": "Công cụ nào trong hệ sinh thái GraphQL chuyên dùng để nhận diện dấu vân tay (Fingerprint) của các engine máy chủ?", "type": "MULTIPLE_CHOICE", "options": ["Nmap", "Graphw00f", "Wireshark", "Metasploit"], "correct_index": 1, "explanation": "Graphw00f nhận dạng engine GraphQL."},
                {"question": "Tiện ích mở rộng nào trên Burp Suite giúp tự động tạo danh sách Queries và Mutations từ Schema GraphQL?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["InQL", "inql"]}], "explanation": "InQL (Doyensec)."},
                {"question": "Nếu tính năng Introspection bị tắt, việc tìm hiểu cấu trúc Schema của GraphQL là hoàn toàn bất khả thi?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Công cụ như Clairvoyance có thể phục hồi Schema qua Field Suggestion."}
            ]
        ),
        (
            4,
            "Bài 5.4: Phân Tích Bề Mặt Tấn Công GraphQL: Queries, Mutations, Directives & Fragments",
            "Mổ xẻ các khối xây dựng của ngôn ngữ GraphQL: Cú pháp Operation Names, Arguments, Aliases, Fragments, Variables, Directives và bề mặt rủi ro tương ứng.",
            "https://www.youtube.com/watch?v=viWzbPuGqpo",
            [
                "Nắm vững cú pháp chi tiết của các thao tác: Query (đọc), Mutation (ghi) và Subscription (thời gian thực).",
                "Hiểu rõ cơ chế đặt bí danh (Aliases) và sử dụng mảnh tái sử dụng (Fragments).",
                "Phân tích cách các tính năng hợp lệ của ngôn ngữ có thể bị vũ khí hóa thành công cụ tấn công."
            ],
            [
                (
                    "Ba Loại Thao Tác Cốt Lõi (Root Operations)",
                    "Mọi hành động trong GraphQL đều bắt đầu từ 3 loại thao tác chính: 1. **Query**: Tương đương với phương thức `GET` trong REST, dùng để truy vấn đọc dữ liệu mà không làm thay đổi trạng thái hệ thống. 2. **Mutation**: Tương đương với các phương thức `POST`, `PUT`, `DELETE` trong REST, dùng để tạo mới dữ liệu (tạo tài khoản), sửa đổi dữ liệu (đổi mật khẩu) hoặc xóa dữ liệu. Đây là mục tiêu tấn công hàng đầu cho các lỗ hổng phân quyền và tiêm nhiễm mã. 3. **Subscription**: Thiết lập kết nối hai chiều thời gian thực (thường qua WebSocket) để máy chủ chủ động đẩy dữ liệu về cho client khi có sự kiện mới (tin nhắn mới, thông báo biến động giá)."
                ),
                (
                    "Vũ Khí Hóa Tính Năng Đặt Bí Danh (Aliases)",
                    "Theo đặc tả GraphQL, bạn không thể truy vấn cùng một trường dữ liệu nhiều lần với các đối số khác nhau trong cùng một câu lệnh. Để vượt qua điều này, GraphQL cung cấp tính năng **Aliases (Bí danh)**: Cho phép đổi tên trường kết quả trả về. Ví dụ: `firstUser: user(id: 1) { name }` và `secondUser: user(id: 2) { name }`. Kẻ tấn công có thể vũ khí hóa tính năng này bằng cách nhồi hàng nghìn bí danh vào MỘT request HTTP duy nhất để thực hiện tấn công vét cạn mật khẩu hoặc vét sạch toàn bộ cơ sở dữ liệu mà không bị tường lửa WAF phát hiện!"
                ),
                (
                    "Các Thành Phần Bổ Trợ: Fragments, Variables & Directives",
                    "- **Fragments**: Đoạn cấu trúc trường tái sử dụng, giúp viết truy vấn gọn hơn nhưng có thể bị lợi dụng để tạo vòng lặp đệ quy gây tràn bộ nhớ. - **Variables**: Tách biệt giữa cấu trúc truy vấn tĩnh và giá trị tham số động truyền vào dưới dạng JSON, giúp bảo vệ chống lại một số lỗi tiêm nhiễm chuỗi thô. - **Directives** (`@include`, `@skip`): Cho phép điều khiển luồng thực thi trường dữ liệu dựa trên điều kiện logic."
                )
            ],
            "Kịch bản tấn công: Bỏ Qua Giới Hạn Tốc Độ (Rate-Limit Bypass) Bằng Aliases: Hệ thống giới hạn mỗi địa chỉ IP chỉ được gửi tối đa 5 request đăng nhập mỗi phút. Tin tặc gửi đúng 1 request HTTP duy nhất chứa 500 bí danh `check1: login(...)`, `check2: login(...)`... Máy chủ xử lý tuần tự 500 lần đăng nhập bên trong nhưng tường lửa chỉ đếm là 1 request, phá vỡ hoàn toàn cơ chế Rate Limiting!",
            "Thực hành viết truy vấn sử dụng Aliases và Fragments kiểm tra trên DVGA:",
            ("graphql", """# Truy vấn đồng thời hai tài khoản khác nhau trong 1 lệnh duy nhất bằng Aliases và Fragment
fragment UserDetails on User {
  id
  username
  email
}

query GetMultipleUsers {
  adminUser: getUser(id: 1) {
    ...UserDetails
  }
  guestUser: getUser(id: 2) {
    ...UserDetails
  }
}"""),
            ["Luôn kiểm tra xem hệ thống có giới hạn số lượng Aliases trong một truy vấn hay không.", "Lưu ý rằng Mutation có thể được thực thi tuần tự trong khi Query có thể chạy song song."],
            ["Query dùng để đọc, Mutation dùng để ghi, Subscription dùng cho WebSocket thời gian thực.", "Aliases cho phép đổi tên trường và gộp nhiều truy vấn vào một request.", "Tính năng Aliases thường bị lợi dụng để qua mặt Rate Limiting."],
            [
                {"question": "Thao tác nào trong GraphQL được sử dụng để tạo mới, cập nhật hoặc xóa dữ liệu trên máy chủ?", "type": "MULTIPLE_CHOICE", "options": ["Query", "Mutation", "Subscription", "Fragment"], "correct_index": 1, "explanation": "Mutation chịu trách nhiệm sửa đổi dữ liệu."},
                {"question": "Tính năng nào của GraphQL cho phép gọi một trường nhiều lần với các đối số khác nhau trong cùng một truy vấn?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Aliases", "alias", "aliases", "Bí danh"]}], "explanation": "Tính năng Aliases (Bí danh)."},
                {"question": "Tất cả các trường trong một Mutation luôn luôn được máy chủ thực thi song song cùng một lúc?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Theo đặc tả GraphQL, các trường trong Mutation bắt buộc phải thực thi tuần tự (serial execution)."}
            ]
        )
    ]

    for (pos, title, summary, v_url, obj_pts, theory_secs, att_def, lab_inst, code_snip, pits, sums, q_json) in configs:
        l = {
            "position": pos,
            "title": title,
            "summary": summary,
            "duration_minutes": 35,
            "video_url": v_url,
            "markdown_content": generate_lesson_markdown(
                lesson_num=f"5.{pos}",
                title=title,
                objective_points=obj_pts,
                theory_sections=theory_secs,
                attack_defense_section=att_def,
                lab_instructions=lab_inst,
                code_snippet=code_snip,
                pitfalls=pits,
                summary_points=sums,
                video_url=v_url,
                quiz_json=q_json,
            )
        }
        validate_lesson_data(l)
        lessons.append(l)

    # Lessons 5.5 to 5.12
    configs_part2 = [
        (
            5,
            "Bài 5.5: Kỹ Thuật Trinh Sát & Nhận Diện Endpoint GraphQL Bằng Nmap & Fingerprinting",
            "Phương pháp luận trinh sát mục tiêu: Quét dò tìm các đường dẫn endpoint phổ biến, sử dụng Nmap NSE script `http-graphql-introspection` và phân tích mã phản hồi đặc thù.",
            "https://www.youtube.com/watch?v=jyjGneKJynk",
            [
                "Nắm vững danh sách các đường dẫn endpoint GraphQL phổ biến nhất trong thực tế.",
                "Sử dụng công cụ Nmap kết hợp script NSE để tự động phát hiện GraphQL trên mạng diện rộng.",
                "Phân tích các phản hồi HTTP đặc thù để xác nhận sự hiện diện của GraphQL kể cả khi bị ẩn giấu."
            ],
            [
                (
                    "Thách Thức Trinh Sát: Endpoint Ẩn Giấu",
                    "Không giống như các trang web thông thường có các liên kết hiển thị rõ ràng trên giao diện, một endpoint GraphQL có thể nằm âm thầm tại các đường dẫn ngầm mà mắt thường không thấy được. Do nhà phát triển thường gộp API vào một đường dẫn riêng phục vụ ứng dụng di động (Mobile App) hoặc giao diện Single Page Application (SPA), nhiệm vụ đầu tiên của chuyên gia kiểm thử là dò tìm ra vị trí chính xác của endpoint đó."
                ),
                (
                    "Danh Sách Các Đường Dẫn Endpoint Phổ Biến Nhất (Common Endpoints)",
                    "Các cuộc khảo sát bảo mật quy mô lớn chỉ ra rằng hơn 95% các triển khai GraphQL đều nằm ở một trong các đường dẫn sau: `/graphql`, `/api/graphql`, `/v1/graphql`, `/v2/graphql`, `/query`, `/api/query`, `/api`, `/altair`, `/playground`, `/graphiql`, `/explorer`. Các công cụ quét như FFUF, Gobuster hoặc Nmap sử dụng các danh sách từ khóa (Wordlists) này để gửi các yêu cầu kiểm tra tự động."
                ),
                (
                    "Phân Tích Dấu Vết Phản Hồi Đặc Thù: Kỹ Thuật `__typename`",
                    "Làm thế nào để xác nhận một URL thực sự là GraphQL chứ không phải là một trang 404 tùy biến? Kỹ thuật phổ biến nhất là gửi một payload JSON chứa trường meta đặc thù **`__typename`**: `{\"query\": \"{ __typename }\"}`. Nếu máy chủ phản hồi mã JSON dạng: `{\"data\": {\"__typename\": \"Query\"}}`, chúng ta có bằng chứng 100% không thể chối cãi rằng endpoint đó là một GraphQL server đang hoạt động!"
                )
            ],
            "Kịch bản trinh sát thực tế: Phát Hiện Endpoint Dành Riêng Cho Ứng Dụng Di Động: Một ngân hàng cấu hình trang web chính chạy REST API, nhưng ứng dụng di động iOS/Android lại kết nối về đường dẫn ngầm `https://api.bank.com/v1/graphql`. Bằng cách phân tích lưu lượng mạng của ứng dụng di động qua Burp Suite, chuyên gia pentest phát hiện endpoint này và mở ra toàn bộ bề mặt tấn công mới.",
            "Thực hành quét tự động phát hiện endpoint GraphQL bằng Nmap và cURL:",
            ("bash", """# 1. Quét phát hiện endpoint GraphQL bằng cURL với trường __typename
curl -s -X POST http://127.0.0.1:5013/graphql \\
     -H "Content-Type: application/json" \\
     -d '{"query": "{ __typename }"}' | jq .

# 2. Sử dụng Nmap NSE script kiểm tra khả năng Introspection của mục tiêu
nmap -p 5013 --script http-graphql-introspection 127.0.0.1"""),
            ["Luôn kiểm tra cả phương thức GET và POST vì một số máy chủ GraphQL hỗ trợ nhận truy vấn qua query parameter trên URL.", "Không chỉ kiểm tra tên miền chính, luôn mở rộng trinh sát sang các subdomain dạng api.*, dev.*, staging.*."],
            ["Hơn 95% endpoint GraphQL nằm ở các đường dẫn phổ biến như /graphql hoặc /api/graphql.", "Truy vấn { __typename } là dấu vân tay vàng xác định máy chủ GraphQL.", "Nmap NSE script hỗ trợ tự động hóa phát hiện GraphQL trên diện rộng."],
            [
                {"question": "Trường siêu dữ liệu (meta-field) nào trong GraphQL thường được dùng để gửi thăm dò xác nhận endpoint tồn tại?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["__typename", "__typename field"]}], "explanation": "Trường __typename phản hồi tên của root type."},
                {"question": "Đường dẫn nào sau đây là endpoint phổ biến nhất của máy chủ GraphQL?", "type": "MULTIPLE_CHOICE", "options": ["/graphql", "/admin.php", "/wp-login", "/cgi-bin"], "correct_index": 0, "explanation": "/graphql là đường dẫn chuẩn mặc định."},
                {"question": "Máy chủ GraphQL chỉ chấp nhận duy nhất phương thức HTTP POST, hoàn toàn không bao giờ chấp nhận HTTP GET?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Nhiều máy chủ GraphQL hỗ trợ nhận truy vấn qua HTTP GET với tham số ?query=..."}
            ]
        ),
        (
            6,
            "Bài 5.6: Khai Thác Tính Năng Introspection Để Bóc Tách Toàn Bộ Sơ Đồ Schema Bí Mật",
            "Mổ xẻ tính năng Introspection của GraphQL: Tự động trích xuất toàn bộ cấu trúc cơ sở dữ liệu nội bộ, trực quan hóa bằng GraphQL Voyager và kỹ thuật bypass khi bị chặn.",
            "https://www.youtube.com/watch?v=viWzbPuGqpo",
            [
                "Hiểu rõ bản chất kỹ thuật của tính năng Nội soi (Introspection System).",
                "Thực hành gửi truy vấn Full Introspection Query để tải về toàn bộ Schema dạng JSON.",
                "Trực quan hóa cấu trúc dữ liệu đồ thị bằng công cụ GraphQL Voyager và phục hồi Schema khi Introspection bị tắt."
            ],
            [
                (
                    "Introspection Là Gì? Con Dao Hai Lưỡi Của GraphQL",
                    "Một trong những tính năng được các nhà phát triển yêu thích nhất của GraphQL là **Introspection (Tự nội soi)**: Cho phép bất kỳ ai cũng có thể truy vấn chính bản thân máy chủ GraphQL để yêu cầu máy chủ giải thích toàn bộ cấu trúc bên trong của nó: Danh sách tất cả các bảng dữ liệu, tên tất cả các trường, kiểu dữ liệu, các tham số đầu vào, và toàn bộ các hàm Mutation đang có sẵn. Trong giai đoạn phát triển (Development), Introspection là công cụ tuyệt vời để các lập trình viên Frontend đọc tài liệu tự động. Nhưng khi đưa lên Production, nếu tính năng này không bị tắt, nó sẽ trở thành một thảm họa an ninh: Tin tặc chỉ cần gửi một truy vấn duy nhất là có trong tay toàn bộ 'bản thiết kế kiến trúc' (Blueprint) của hệ thống!"
                ),
                (
                    "Cấu Trúc Truy Vấn Full Introspection Query",
                    "Bằng cách truy vấn trường meta `__schema` và `__type`, kẻ tấn công có thể bóc tách toàn bộ hệ thống: `query IntrospectionQuery { __schema { queryType { name } mutationType { name } types { name fields { name type { name } } } } }`. Kết quả trả về là một tệp JSON khổng lồ mô tả chi tiết từng ngóc ngách của ứng dụng, bao gồm cả các hàm nội bộ nguy hiểm mà giao diện web thông thường không bao giờ hiển thị (ví dụ: `deleteUser`, `updateUserRole`, `resetDatabase`)."
                ),
                (
                    "Trực Quan Hóa Với GraphQL Voyager & SpectaQL",
                    "Sau khi trích xuất được tệp JSON Introspection, chuyên gia pentest nạp tệp này vào công cụ trực quan hóa **GraphQL Voyager**. Voyager sẽ tự động vẽ ra một bản đồ mạng đồ thị tương tác tuyệt đẹp, hiển thị toàn bộ mối quan hệ liên kết giữa các bảng dữ liệu, giúp chuyên gia nhanh chóng xác định các thực thể nhạy cảm như `User`, `Payment`, `AdminRole` để tập trung tấn công."
                )
            ],
            "Kịch bản thực chiến: Phục Hồi Schema Khi Introspection Bị Tắt (Bypass Disabled Introspection): Quản trị viên tắt Introspection. Tuy nhiên, họ vẫn để bật cơ chế 'Did you mean...?' (Gợi ý sửa lỗi chính tả của GraphQL). Chuyên gia sử dụng công cụ Clairvoyance: Gửi hàng nghìn từ khóa thử nghiệm; khi nhập sai từ, máy chủ phản hồi: `Cannot query field 'passwor'. Did you mean 'password'?`. Clairvoyance tự động thu thập các gợi ý này để tái dựng lại 100% cấu trúc Schema mà không cần Introspection!",
            "Thực hành trích xuất Schema đầy đủ từ máy chủ DVGA bằng lệnh cURL:",
            ("bash", """# Gửi truy vấn Introspection cơ bản để trích xuất danh sách tất cả các kiểu dữ liệu
curl -s -X POST http://127.0.0.1:5013/graphql \\
     -H "Content-Type: application/json" \\
     -d '{"query": "{ __schema { types { name kind } } }"}' | jq .data.__schema.types[0..10]"""),
            ["Bắt buộc tắt hoàn toàn tính năng Introspection trên môi trường Production.", "Vô hiệu hóa tính năng Field Suggestion trên các engine như Apollo để chống công cụ Clairvoyance."],
            ["Introspection cung cấp toàn bộ bản thiết kế Schema cho bất kỳ ai truy vấn.", "Để lộ Introspection trên Production tương đương với việc công khai mã nguồn kiến trúc dữ liệu.", "Công cụ Clairvoyance có thể phục hồi Schema qua cơ chế Field Suggestion khi Introspection bị tắt."],
            [
                {"question": "Trường siêu dữ liệu nào được sử dụng để truy vấn thông tin toàn bộ cấu trúc Schema của GraphQL?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["__schema", "__schema field"]}], "explanation": "Trường __schema."},
                {"question": "Công cụ đồ họa nào cho phép biến tệp JSON Introspection thành bản đồ đồ thị tương tác trực quan?", "type": "MULTIPLE_CHOICE", "options": ["GraphQL Voyager", "Photoshop", "Nmap", "Wireshark"], "correct_index": 0, "explanation": "GraphQL Voyager."},
                {"question": "Tắt tính năng Introspection trên môi trường Production là một khuyến nghị an ninh bắt buộc?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Tắt Introspection là biện pháp cơ bản bảo vệ Schema trên production."}
            ]
        ),
        (
            7,
            "Bài 5.7: Tấn Công Từ Chối Dịch Vụ (DoS) Qua Truy Vấn Đệ Quy Vô Hạn (Circular Query DoS)",
            "Khai thác cấu trúc dữ liệu đồ thị quan hệ hai chiều: Tấn công từ chối dịch vụ (DoS) bằng truy vấn đệ quy vô hạn (Deeply Nested Queries), làm cạn kiệt CPU và bộ nhớ RAM máy chủ.",
            "https://www.youtube.com/watch?v=jyjGneKJynk",
            [
                "Nắm vững nguyên lý của các mối quan hệ vòng tròn (Circular / Recursive Relationships) trong đồ thị GraphQL.",
                "Thực hành xây dựng payload tấn công lồng ghép đệ quy sâu (Deeply Nested Query DoS).",
                "Triển khai các biện pháp phòng vệ: Phân tích độ sâu truy vấn (Max Depth Limiting) và Query Cost Analysis."
            ],
            [
                (
                    "Bản Chất Kỹ Thuật Của Mối Quan Hệ Vòng Tròn (Circular References)",
                    "Trong thiết kế cơ sở dữ liệu đồ thị, các mối quan hệ hai chiều là rất phổ biến và hoàn toàn tự nhiên: Một `Author` (Tác giả) có thể viết nhiều `Post` (Bài viết); Và mỗi `Post` lại có trường tham chiếu ngược về `Author`. Trong kiến trúc REST, việc truy vấn đệ quy này bị chặn lại do cấu trúc endpoint cố định. Nhưng trong GraphQL, do máy khách có toàn quyền chỉ định các trường lồng nhau, điều gì sẽ xảy ra nếu kẻ tấn công gửi một truy vấn có cấu trúc: Tác giả -> Bài viết -> Tác giả -> Bài viết -> Tác giả... lặp lại hàng nghìn lần?"
                ),
                (
                    "Cơ Chế Gây Kiệt Quệ Tài Nguyên Máy Chủ (Resource Exhaustion DoS)",
                    "Khi nhận được một truy vấn đệ quy lồng nhau 100 tầng: Trình phân tích cú pháp (Query Parser) của GraphQL phải tạo ra một Cây cú pháp trừu tượng (Abstract Syntax Tree - AST) khổng lồ trong bộ nhớ RAM. Sau đó, máy chủ thực thi hàng triệu hàm Resolver lồng nhau, gửi hàng triệu câu truy vấn SQL con tới cơ sở dữ liệu backend. Chỉ với MỘT request HTTP duy nhất nặng chưa đầy 2 KB gửi lên từ máy client, máy chủ có thể bị chiếm dụng 100% CPU, cạn kiệt toàn bộ RAM và bị sập hoàn toàn (Crash), từ chối phục vụ mọi người dùng hợp pháp khác!"
                ),
                (
                    "Các Chiến Lược Phòng Thủ Toàn Diện",
                    "Để ngăn chặn cuộc tấn công hủy diệt này, đội ngũ phát triển bắt buộc phải triển khai hai lớp lá chắn: 1. Giới Hạn Độ Sâu Truy Vấn (Max Query Depth Limiting): Sử dụng thư viện như `graphql-depth-limit` để từ chối ngay lập tức mọi truy vấn có độ lồng nhau vượt quá một ngưỡng an toàn (ví dụ tối đa 5 hoặc 6 tầng). 2. Phân Tích Chi Phí Truy Vấn (Query Cost Analysis): Gán cho mỗi trường một điểm số chi phí tính toán (Complexity Score) và từ chối các truy vấn có tổng điểm vượt quá giới hạn."
                )
            ],
            "Kịch bản tấn công DoS thực tế: Đánh Sập Ứng Dụng Thương Mại Điện Tử Trong Ngày Giảm Giá: Kẻ tấn công gửi liên tục 50 request chứa truy vấn đệ quy lồng nhau 50 tầng giữa `Product` và `Category`. Máy chủ Node.js/Apollo bị nghẽn Event Loop hoàn toàn, cơ sở dữ liệu PostgreSQL bị cạn kiệt connection pool, khiến toàn bộ hệ thống thanh toán bị tê liệt.",
            "Thực hành xây dựng payload kiểm thử độ sâu truy vấn trên máy chủ DVGA:",
            ("graphql", """# Payload kiểm thử tấn công Circular Query DoS
query MaliciousCircularQuery {
  pastes {
    owner {
      pastes {
        owner {
          pastes {
            owner {
              id
              username
            }
          }
        }
      }
    }
  }
}"""),
            ["Luôn cấu hình thư viện graphql-depth-limit trong pipeline xử lý validation của máy chủ GraphQL.", "Không bao giờ để mặc định độ sâu truy vấn là vô hạn."],
            ["Quan hệ hai chiều trong GraphQL tạo ra nguy cơ tấn công đệ quy vô hạn.", "Một request nhỏ có thể kích hoạt hàng triệu truy vấn backend làm sập máy chủ.", "Max Depth Limiting và Query Complexity là giải pháp phòng vệ bắt buộc."],
            [
                {"question": "Kỹ thuật phòng thủ nào trong GraphQL giúp từ chối các truy vấn có cấu trúc lồng nhau vượt quá số tầng cho phép?", "type": "MULTIPLE_CHOICE", "options": ["Max Query Depth Limiting", "SQL Injection Filter", "CORS Configuration", "HTTPS Enforcement"], "correct_index": 0, "explanation": "Max Query Depth Limiting khống chế độ sâu lồng nhau của truy vấn."},
                {"question": "Một truy vấn đệ quy sâu trong GraphQL có thể làm sập máy chủ chỉ với duy nhất một request HTTP?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Cấu trúc đệ quy kích hoạt hàng triệu resolver gây cạn kiệt tài nguyên."},
                {"question": "Thư viện phổ biến nào trong hệ sinh thái Node.js/GraphQL được dùng để giới hạn độ sâu truy vấn?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["graphql-depth-limit", "depth-limit"]}], "explanation": "graphql-depth-limit."}
            ]
        ),
        (
            8,
            "Bài 5.8: Tấn Công Vét Cạn & Vượt Ngưỡng Giới Hạn Tốc Độ (Rate-Limit Bypass) Bằng Aliases",
            "Vũ khí hóa tính năng Aliases và Batching: Kỹ thuật nhồi hàng nghìn thao tác vào một HTTP request duy nhất để vét cạn mật khẩu, mã OTP và vượt qua mọi tường lửa Rate Limiting.",
            "https://www.youtube.com/watch?v=viWzbPuGqpo",
            [
                "Nắm vững cơ chế hoạt động của tấn công GraphQL Batching và Aliasing Abuse.",
                "Sử dụng công cụ CrackQL để tự động hóa vét cạn thông tin đăng nhập qua GraphQL.",
                "Triển khai các biện pháp phòng vệ: Batch Request Limiting và Per-Field Rate Limiting."
            ],
            [
                (
                    "Cơ Chế Bỏ Qua Tường Lửa Giới Hạn Tần Suất (Rate Limiting)",
                    "Các hệ sinh thái an ninh mạng truyền thống (WAF, Nginx, Cloudflare) đều đo lường tần suất dựa trên số lượng Yêu cầu HTTP (HTTP Requests per second/minute). Ví dụ: 'Chặn IP nếu gửi quá 5 request POST tới `/login` trong 1 phút'. Trong GraphQL, tư duy phòng thủ này hoàn toàn bị phá sản! GraphQL hỗ trợ hai cơ chế gộp thao tác: 1. Array Batching: Gửi một mảng JSON chứa nhiều truy vấn độc lập: `[{\"query\": \"...\"}, {\"query\": \"...\"}]`. 2. Mutation Aliasing: Nhồi hàng trăm Mutation vào cùng một câu lệnh duy nhất bằng cách đặt các bí danh khác nhau: `mutation { a: login(...) b: login(...) c: login(...) }`."
                ),
                (
                    "Kịch Bản Tấn Công Vét Cạn Mã Xác Thực OTP 2FA",
                    "Hãy tưởng tượng một ngân hàng gửi mã xác thực OTP gồm 4 chữ số (từ 0000 đến 9999) qua SMS. Trong REST, bạn không thể vét cạn vì sau 3 lần nhập sai tài khoản sẽ bị khóa. Nhưng trên GraphQL: Kẻ tấn công tạo ra một truy vấn duy nhất chứa đúng 10,000 bí danh từ `attempt0000: verifyOtp(code: \"0000\")` đến `attempt9999: verifyOtp(code: \"9999\")`. Khi gửi request này lên máy chủ, tường lửa chỉ đếm là 1 request duy nhất! Máy chủ xử lý toàn bộ 10,000 mã và một trong số các bí danh đó sẽ trả về kết quả thành công, bẻ khóa tài khoản trong chưa đầy 3 giây!"
                ),
                (
                    "Các Giải Pháp Phòng Vệ Chuyên Sâu",
                    "Để ngăn chặn kỹ thuật Aliasing Abuse, hệ thống phòng thủ phải áp dụng: Giới hạn số lượng Aliases tối đa được phép xuất hiện trong một truy vấn (ví dụ tối đa 5 hoặc 10 aliases); Vô hiệu hóa tính năng Array Batching nếu không có nhu cầu sử dụng; Và quan trọng nhất: Áp dụng cơ chế **Rate Limiting theo mức độ nghiệp vụ (Business-level Rate Limiting)** dựa trên số lần gọi hàm Mutation thay vì đếm số lượng HTTP request."
                )
            ],
            "Kịch bản thực chiến: Sử Dụng CrackQL Để Vét Cạn Mật Khẩu Siêu Tốc: Chuyên gia an ninh sử dụng công cụ CrackQL: nạp danh sách 1,000 mật khẩu phổ biến nhất, CrackQL tự động chia thành các gói 100 aliases mỗi request và tìm ra mật khẩu tài khoản quản trị chỉ sau 10 request HTTP mà hoàn toàn không bị WAF chặn IP.",
            "Thực hành viết payload kiểm thử vét cạn nhiều mật khẩu bằng Aliases trên DVGA:",
            ("graphql", """# Payload vét cạn đồng thời 3 mật khẩu khác nhau trong 1 request duy nhất
mutation BruteForceLogin {
  try1: login(username: "admin", password: "Password123") {
    token
    error
  }
  try2: login(username: "admin", password: "AdminPassword") {
    token
    error
  }
  try3: login(username: "admin", password: "correct_password") {
    token
    error
  }
}"""),
            ["Tuyệt đối không cấu hình Rate Limiting chỉ dựa trên số lượng HTTP request ở tầng proxy Nginx/WAF.", "Khống chế số lượng Aliases và thao tác Batching trong cấu hình engine GraphQL."],
            ["Aliases và Batching cho phép gộp hàng nghìn thao tác vào một HTTP request duy nhất.", "Kỹ thuật này dễ dàng bẻ gãy các hệ thống chống Brute-force và bảo vệ mã OTP truyền thống.", "Cần triển khai Rate Limiting ở cấp độ hàm nghiệp vụ Resolver."],
            [
                {"question": "Kỹ thuật nào trong GraphQL cho phép kẻ tấn công gộp hàng trăm lần đăng nhập vào một HTTP request duy nhất để qua mặt WAF?", "type": "MULTIPLE_CHOICE", "options": ["Aliases Abuse / Batching", "SQL Injection", "XSS", "CSRF"], "correct_index": 0, "explanation": "Aliases Abuse và Batching."},
                {"question": "Công cụ mã nguồn mở chuyên dụng nào được thiết kế để tự động hóa tấn công Brute-force qua GraphQL bằng Aliasing?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["CrackQL", "crackql"]}], "explanation": "Công cụ CrackQL."},
                {"question": "Đếm số lượng HTTP request ở tầng Nginx là đủ để ngăn chặn tấn công vét cạn mật khẩu trên GraphQL?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Tin tặc có thể gộp hàng nghìn phép thử vào một HTTP request duy nhất."}
            ]
        ),
        (
            9,
            "Bài 5.9: Khai Thác Lỗ Hổng Kiểm Soát Truy Cập (Broken Object-Level Authorization - BOLA/IDOR)",
            "Nghiên cứu lỗ hổng nguy hiểm số 1 của API (OWASP API Top 10): Phân tích lỗi thiếu kiểm tra quyền sở hữu đối tượng ở tầng Resolver, khai thác IDOR và trích xuất dữ liệu người dùng trái phép.",
            "https://www.youtube.com/watch?v=jyjGneKJynk",
            [
                "Nắm vững nguyên lý của lỗ hổng BOLA (Broken Object-Level Authorization) / IDOR trong GraphQL.",
                "Giải mã sai lầm phổ biến của lập trình viên khi phụ thuộc vào bảo mật của tầng Schema.",
                "Thực hành khai thác và vá lỗ hổng BOLA trên các hàm Query và Mutation."
            ],
            [
                (
                    "Lỗ Hổng Nguy Hiểm Số 1 Của Thế Giới API: BOLA / IDOR",
                    "Trong danh mục OWASP API Security Top 10, **Broken Object-Level Authorization (BOLA - Lỗi phân quyền cấp đối tượng)**, hay còn gọi là Insecure Direct Object References (IDOR), luôn giữ vị trí quán quân về mức độ tàn phá và tần suất xuất hiện. Lỗ hổng này xảy ra khi ứng dụng cho phép người dùng truy cập hoặc thao tác trên một đối tượng dữ liệu cụ thể (ví dụ: hóa đơn thanh toán, hồ sơ y tế, bài viết riêng tư) chỉ bằng cách truyền vào mã định danh (ID) của đối tượng đó mà **không kiểm tra xem người dùng hiện tại có thực sự sở hữu hoặc có quyền xem đối tượng đó hay không**."
                ),
                (
                    "Sai Lầm Tai Hại: Nhầm Lẫn Giữa Type Safety & Authorization",
                    "Các nhà phát triển mới tiếp cận GraphQL thường có ảo tưởng rằng: Vì GraphQL có hệ thống kiểm tra kiểu dữ liệu (Type System) rất chặt chẽ, nên ứng dụng tự động được an toàn. Đây là một ngộ nhận chết người! Trình biên dịch GraphQL chỉ đảm bảo rằng đối số `id` truyền vào là kiểu số nguyên `Int` hoặc chuỗi `ID` hợp lệ, nó hoàn toàn KHÔNG THỂ biết được liệu người dùng ID 5 có quyền xem hóa đơn của người dùng ID 6 hay không. Trách nhiệm kiểm tra phân quyền này thuộc về 100% logic mã nguồn bên trong hàm **Resolver Function**."
                ),
                (
                    "Kịch Bản Khai Thác BOLA Trên Query & Mutation",
                    "- BOLA trên Query: Người dùng đăng nhập với tài khoản Bob (ID=102). Bob gửi truy vấn: `query { getInvoice(id: 105) { totalAmount creditCardNumber } }`. Máy chủ trả về toàn bộ thông tin thẻ tín dụng của nạn nhân Alice (ID=105). - BOLA trên Mutation: Người dùng gửi yêu cầu sửa đổi: `mutation { updateEmail(userId: 1, newEmail: \"hacker@evil.com\") }`. Máy chủ thực thi ngay lập tức, chuyển quyền sở hữu tài khoản Admin (ID=1) sang cho kẻ tấn công!"
                )
            ],
            "Phương pháp phòng thủ chuẩn mực: Không bao giờ tin tưởng ID do máy khách gửi lên! Hàm Resolver bắt buộc phải trích xuất danh tính của người dùng từ phiên xác thực an toàn (`context.user.id`) và so sánh với quyền sở hữu đối tượng trong cơ sở dữ liệu trước khi trả về kết quả.",
            "Thực hành kiểm thử lỗ hổng BOLA/IDOR trên hàm lấy thông tin ghi chú riêng tư của DVGA:",
            ("graphql", """# Truy vấn kiểm tra xem có thể đọc ghi chú riêng tư của người khác bằng cách thay đổi pasteId hay không
query ReadPrivatePaste {
  getPaste(pasteId: 1) {
    id
    title
    content
    isPrivate
    owner {
      username
    }
  }
}"""),
            ["Luôn kiểm tra quyền truy cập ở từng hàm Resolver riêng biệt; không phó mặc việc phân quyền cho tầng mạng bên ngoài.", "Sử dụng các định danh ngẫu nhiên không đoán được (UUID v4) thay vì số nguyên tăng dần (Sequential IDs) để giảm thiểu rủi ro dò quét."],
            ["BOLA/IDOR là lỗ hổng phổ biến và nguy hiểm nhất trên các hệ thống API hiện đại.", "Hệ thống kiểu dữ liệu của GraphQL không thay thế được logic kiểm tra phân quyền trong Resolver.", "Luôn xác thực quyền sở hữu của người dùng hiện tại trước khi trả về hoặc sửa đổi dữ liệu."],
            [
                {"question": "Lỗ hổng BOLA (Broken Object-Level Authorization) xảy ra do thiếu sót kiểm tra an ninh ở tầng nào?", "type": "MULTIPLE_CHOICE", "options": ["Tầng Schema", "Tầng hàm phân giải (Resolver Function)", "Tầng giao thức HTTP", "Tầng phân giải DNS"], "correct_index": 1, "explanation": "BOLA xảy ra do hàm Resolver không kiểm tra quyền sở hữu đối tượng."},
                {"question": "Sử dụng UUID v4 ngẫu nhiên thay cho ID số nguyên tăng dần có thể giúp giảm thiểu nguy cơ bị quét dò IDOR?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. UUID khó đoán hơn nhiều so với số nguyên tăng dần 1, 2, 3..."},
                {"question": "Tên viết tắt kinh điển khác của lỗ hổng BOLA trong bảng xếp hạng OWASP truyền thống là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["IDOR", "idor"]}], "explanation": "Insecure Direct Object References (IDOR)."}
            ]
        ),
        (
            10,
            "Bài 5.10: Tấn Công Tiêm Nhiễm (Injection Flaws): SQLi, NoSQLi & Command Injection Qua GraphQL",
            "Mổ xẻ các kịch bản tiêm mã độc vào tham số truy vấn GraphQL: Tiêm nhiễm cơ sở dữ liệu SQL Injection, NoSQL Injection và thực thi lệnh hệ điều hành Command Injection.",
            "https://www.youtube.com/watch?v=viWzbPuGqpo",
            [
                "Hiểu rõ cơ chế các tham số GraphQL trở thành đầu vào nguy hiểm cho các lệnh SQL/NoSQL backend.",
                "Thực hành khai thác lỗi SQL Injection trong các hàm Query/Mutation trên DVGA.",
                "Áp dụng nguyên tắc Parameterized Queries và ORM chuẩn để triệt tiêu hoàn toàn lỗi Injection."
            ],
            [
                (
                    "GraphQL Có Miễn Nhiễm Với Tấn Công Tiêm Nhiễm (Injection) Không?",
                    "Một ngộ nhận cực kỳ phổ biến của các nhà phát triển là: 'GraphQL là ngôn ngữ truy vấn hiện đại, do đó nó không thể bị dính SQL Injection'. Thực tế hoàn toàn ngược lại: GraphQL CHỈ LÀ MỘT LỚP TRUYỀN THÔNG (Transport Layer) nằm ở phía trước. Phía sau hàm Resolver, ứng dụng vẫn bắt buộc phải kết nối tới cơ sở dữ liệu quan hệ (PostgreSQL, MySQL, SQL Server) hoặc NoSQL (MongoDB). Nếu nhà phát triển lấy đối số từ GraphQL và ghép nối chuỗi thô (String Concatenation) vào câu lệnh SQL, hệ thống sẽ bị dính SQL Injection 100%!"
                ),
                (
                    "Kịch Bản Khai Thác SQL Injection Qua GraphQL Argument",
                    "Giả sử hàm Resolver được viết bằng mã Python cẩu thả như sau: `query = f\"SELECT * FROM users WHERE username = '{args['username']}'\"`. Kẻ tấn công gửi truy vấn GraphQL: `query { getUser(username: \"admin' OR 1=1 --\") { id email } }`. Câu lệnh SQL được tạo ra trở thành: `SELECT * FROM users WHERE username = 'admin' OR 1=1 --'`. Kết quả là máy chủ trả về toàn bộ dữ liệu tài khoản quản trị và danh sách người dùng mà không cần mật khẩu!"
                ),
                (
                    "Tấn Công NoSQL Injection & Command Injection",
                    "- **NoSQL Injection**: Trong các hệ thống sử dụng MongoDB, nếu đầu vào GraphQL chấp nhận kiểu JSON Object mà không kiểm tra chặt chẽ, kẻ tấn công có thể truyền các toán tử đặc biệt của Mongo như `{\"$ne\": null}` hoặc `{\"$regex\": \".*\"}` để bẻ khóa xác thực. - **Command Injection**: Nếu tham số của Mutation được đưa trực tiếp vào hàm gọi hệ điều hành (như `system()`, `exec()`, `os.system()`), kẻ tấn công có thể chèn các ký tự điều khiển `; rm -rf /` hoặc `| cat /etc/passwd` để chiếm quyền điều khiển toàn bộ máy chủ."
                )
            ],
            "Phương pháp phòng thủ tuyệt đối: BẮT BUỘC sử dụng Truy Vấn Có Tham Số Hóa (Parameterized Queries / Prepared Statements) hoặc các thư viện ORM uy tín (SQLAlchemy, Prisma, Entity Framework). Tuyệt đối không bao giờ ghép nối chuỗi để tạo câu lệnh SQL hoặc lệnh hệ điều hành.",
            "Thực hành khai thác lỗ hổng SQL Injection qua tham số GraphQL trên máy chủ DVGA:",
            ("graphql", """# Payload khai thác SQL Injection trích xuất toàn bộ dữ liệu qua tham số tìm kiếm
query ExploitSqlInjection {
  searchPaste(query: "' UNION SELECT 1, username, password, 4, 5 FROM users --") {
    id
    title
    content
  }
}"""),
            ["Tuyệt đối không sử dụng hàm ghép chuỗi string formatting (f-strings, printf) để tạo câu lệnh truy vấn database trong Resolver.", "Sử dụng ORM an toàn và áp dụng nguyên tắc đặc quyền tối thiểu (Least Privilege) cho tài khoản database."],
            ["GraphQL chỉ là lớp trung chuyển; mã nguồn Resolver ghép chuỗi cẩu thả vẫn bị dính SQLi bình thường.", "Prepared Statements là biện pháp duy nhất triệt tiêu hoàn toàn lỗ hổng SQL Injection.", "Cảnh giác với cả NoSQL Injection và Command Injection khi tham số tương tác với hệ điều hành."],
            [
                {"question": "Nguyên nhân cốt lõi dẫn đến lỗ hổng SQL Injection trong ứng dụng GraphQL là gì?", "type": "MULTIPLE_CHOICE", "options": ["Do giao thức GraphQL bị lỗi thiết kế", "Do hàm Resolver ghép chuỗi thô đối số vào câu lệnh SQL", "Do trình duyệt web bị nhiễm virus", "Do mạng Internet bị chậm"], "correct_index": 1, "explanation": "Do lập trình viên ghép chuỗi thô đối số vào lệnh SQL thay vì dùng Prepared Statements."},
                {"question": "Biện pháp kỹ thuật nào giúp triệt tiêu hoàn toàn nguy cơ SQL Injection trong các hàm Resolver?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Prepared Statements", "Parameterized Queries", "prepared statements"]}], "explanation": "Prepared Statements / Parameterized Queries."},
                {"question": "Sử dụng cơ sở dữ liệu NoSQL như MongoDB sẽ giúp ứng dụng miễn nhiễm 100% với các lỗi tiêm nhiễm (Injection)?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Ứng dụng vẫn có thể bị dính NoSQL Injection nếu truyền toán tử độc hại."}
            ]
        ),
        (
            11,
            "Bài 5.11: Khai Thác Lỗ Hổng CSRF & WebSocket Hijacking Trong GraphQL Subscriptions",
            "Nghiên cứu các cuộc tấn công qua trình duyệt: Cross-Site Request Forgery (CSRF) qua phương thức GET/POST trên GraphQL và kỹ thuật chiếm đoạt kết nối WebSocket Subscriptions.",
            "https://www.youtube.com/watch?v=jyjGneKJynk",
            [
                "Hiểu rõ cơ chế lỗ hổng CSRF trên các endpoint GraphQL sử dụng xác thực bằng Cookie.",
                "Giải mã kỹ thuật Cross-Site WebSocket Hijacking (CSWSH) nhằm vào các kênh Subscriptions.",
                "Triển khai các biện pháp bảo vệ: SameSite Cookie, Anti-CSRF Tokens và kiểm tra Origin Header."
            ],
            [
                (
                    "Tại Sao GraphQL Vẫn Có Thể Bị Tấn Công CSRF?",
                    "Nhiều người lầm tưởng rằng: 'GraphQL sử dụng `POST` với `Content-Type: application/json`, do đó nó miễn nhiễm với tấn công CSRF'. Đây là một nhận thức sai lầm nguy hiểm vì 2 lý do: 1. Nhiều máy chủ GraphQL hỗ trợ xử lý truy vấn thông qua phương thức `GET` (`/graphql?query=mutation{...}`). Phương thức GET cực kỳ dễ bị tấn công CSRF thông qua các thẻ HTML đơn giản như `<img src=\"...\">`. 2. Nếu máy chủ chấp nhận các kiểu nội dung đơn giản như `application/x-www-form-urlencoded` hoặc `text/plain` mà không xác thực tiêu đề nghiêm ngặt, kẻ tấn công có thể kích hoạt CSRF thông qua các biểu mẫu HTML tự động gửi (Auto-submitting forms)."
                ),
                (
                    "Cơ Chế Tấn Công Cross-Site Request Forgery (CSRF)",
                    "Khi người dùng đăng nhập vào ứng dụng web và phiên làm việc được lưu trong Cookie trình duyệt: Nạn nhân truy cập vào một trang web độc hại do tin tặc lập ra. Trang web này âm thầm gửi một yêu cầu ngầm tới `POST /graphql` của ứng dụng nạn nhân để thực hiện Mutation đổi mật khẩu hoặc chuyển tiền. Trình duyệt tự động đính kèm Cookie hợp lệ của nạn nhân, khiến máy chủ thực thi giao dịch phi pháp mà nạn nhân hoàn toàn không hay biết!"
                ),
                (
                    "Cross-Site WebSocket Hijacking (CSWSH) Trên Subscriptions",
                    "GraphQL Subscriptions sử dụng giao thức WebSocket (`ws://` hoặc `wss://`) để duy trì kết nối thời gian thực. Trong quá trình bắt tay nâng cấp (WebSocket Handshake), trình duyệt tự động gửi Cookie xác thực. Nếu máy chủ GraphQL không kiểm tra tiêu đề **`Origin Header`**, một trang web độc hại của bên thứ ba có thể thiết lập kết nối WebSocket tới máy chủ của nạn nhân, âm thầm nghe lén toàn bộ luồng dữ liệu thông báo nhạy cảm của nạn nhân theo thời gian thực!"
                )
            ],
            "Phương pháp phòng thủ toàn diện: 1. Tuyệt đối không hỗ trợ thực thi Mutation qua phương thức HTTP GET. 2. Bắt buộc kiểm tra tiêu đề `Content-Type: application/json` và từ chối các loại nội dung khác. 3. Thiết lập thuộc tính Cookie `SameSite=Lax` hoặc `SameSite=Strict`. 4. Luôn kiểm tra nghiêm ngặt tiêu đề `Origin` trong các kết nối WebSocket Handshake.",
            "Thực hành viết trang HTML minh chứng kịch bản tấn công CSRF gửi Mutation tự động:",
            ("html", """<!-- Trang web giả lập tấn công CSRF lên endpoint GraphQL -->
<!DOCTYPE html>
<html>
<body>
    <h1>Trang web trúng thưởng iPhone miễn phí!</h1>
    <form id="csrfForm" action="http://127.0.0.1:5013/graphql" method="POST">
        <!-- Chèn mutation đổi email vào trường dữ liệu thô -->
        <input type="hidden" name="query" value="mutation { changeEmail(newEmail: 'hacker@evil.com') { success } }" />
    </form>
    <script>
        // Tự động submit biểu mẫu khi trang vừa tải xong
        document.getElementById('csrfForm').submit();
    </script>
</body>
</html>"""),
            ["Luôn cấu hình cờ SameSite=Lax hoặc SameSite=Strict cho tất cả các cookie xác thực phiên.", "Kiểm tra tiêu đề Origin trên toàn bộ các kênh kết nối WebSocket Subscriptions."],
            ["GraphQL có thể bị dính CSRF nếu hỗ trợ GET hoặc không kiểm tra Content-Type nghiêm ngặt.", "Cross-Site WebSocket Hijacking (CSWSH) nghe lén dữ liệu Subscriptions nếu thiếu kiểm tra Origin.", "SameSite Cookies và Anti-CSRF Tokens là giải pháp phòng vệ bắt buộc."],
            [
                {"question": "Thuộc tính nào của Cookie giúp ngăn chặn trình duyệt tự động gửi cookie trong các yêu cầu cross-site để chống CSRF?", "type": "MULTIPLE_CHOICE", "options": ["HttpOnly", "Secure", "SameSite (Lax/Strict)", "Domain"], "correct_index": 2, "explanation": "Thuộc tính SameSite=Lax hoặc Strict."},
                {"question": "Tiêu đề HTTP nào bắt buộc phải được máy chủ kiểm tra trong quá trình bắt tay WebSocket để chống tấn công CSWSH?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Origin", "Origin Header", "origin"]}], "explanation": "Tiêu đề Origin."},
                {"question": "Cho phép thực thi các thao tác Mutation sửa đổi dữ liệu thông qua phương thức HTTP GET là một thiết kế an toàn?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Cho phép Mutation qua GET khiến ứng dụng cực kỳ dễ bị tấn công CSRF."}
            ]
        ),
        (
            12,
            "Bài 5.12: Chiến Lược Phòng Thủ Toàn Diện: Hardening GraphQL Schema, Query Cost Analysis & Validation",
            "Đúc kết chiến lược phòng thủ chiều sâu cho GraphQL: Khóa chặn Introspection, phân tích chi phí truy vấn (Query Cost Analysis), cơ chế Safe-Listing và xây dựng hệ thống phòng thủ bất khả xâm phạm.",
            "https://www.youtube.com/watch?v=viWzbPuGqpo",
            [
                "Nắm vững mô hình phòng thủ chiều sâu (Defense-in-Depth) dành riêng cho kiến trúc GraphQL.",
                "Thực hành triển khai thư viện Query Complexity & Cost Analysis trên máy chủ sản xuất.",
                "Áp dụng cơ chế Persisted Queries (Safe-listing) để loại bỏ 99% các cuộc tấn công thăm dò tùy ý."
            ],
            [
                (
                    "Tổng Kết Bề Mặt Rủi Ro & Mô Hình Phòng Thủ Chiều Sâu",
                    "Trải qua toàn bộ 12 bài học của Chương 5, chúng ta đã thấy rằng sự linh hoạt tuyệt vời của GraphQL cũng chính là con dao hai lưỡi mang lại những rủi ro an ninh chưa từng có: Từ việc Schema bị lộ qua Introspection, máy chủ bị sập bởi Circular DoS, giới hạn tốc độ bị bẻ gãy bởi Aliasing, cho đến các lỗ hổng logic BOLA/IDOR và Injection trong hàm Resolver. Để bảo vệ một hệ thống GraphQL doanh nghiệp, người quản trị không thể chỉ dựa vào một giải pháp đơn lẻ mà bắt buộc phải triển khai **Mô hình phòng thủ chiều sâu đa lớp (Defense-in-Depth)**."
                ),
                (
                    "Lớp 1: Khóa Chặt Schema & Cấu Hình Môi Trường Production",
                    "1. Vô hiệu hóa 100% tính năng Introspection trên môi trường Production (`introspection: false`). 2. Vô hiệu hóa giao diện tương tác GraphiQL / Playground. 3. Vô hiệu hóa cơ chế gợi ý sửa lỗi Field Suggestion trên Apollo Server bằng plugin bảo mật. 4. Đảm bảo thông điệp lỗi trả về cho client ở dạng chung chung (`Internal Server Error`), không bao giờ để lộ vết ngăn xếp (Stack Trace) hoặc câu lệnh cơ sở dữ liệu nội bộ."
                ),
                (
                    "Lớp 2: Kiểm Soát Tài Nguyên Bằng Query Cost & Depth Limiting",
                    "Triển khai thuật toán tính toán độ phức tạp trước khi thực thi truy vấn: Giới hạn độ sâu tối đa (Max Depth <= 6); Gán trọng số chi phí cho các danh sách (List fields có chi phí cao hơn Scalar fields); Nếu tổng chi phí của truy vấn vượt quá ngưỡng cho phép (ví dụ > 1000 điểm), máy chủ lập tức từ chối thực thi và phản hồi lỗi HTTP 400 Bad Request."
                ),
                (
                    "Lớp 3: Giải Pháp Tối Thượng: Persisted Queries (Safe-listing)",
                    "Biện pháp bảo vệ tối thượng có khả năng triệt tiêu 99% các cuộc tấn công thăm dò GraphQL là **Persisted Queries (Truy vấn lưu sẵn / Safe-listing)**: 1. Trong quá trình phát triển, toàn bộ các truy vấn hợp lệ của ứng dụng Frontend được trích xuất và băm thành mã SHA-256 (ví dụ: `dc675...`). Danh sách mã băm này được lưu trên máy chủ làm danh sách trắng (Allowlist). 2. Khi chạy thực tế, client KHÔNG BAO GIỜ gửi chuỗi truy vấn GraphQL thô lên mạng. Client chỉ gửi mã băm `{\"id\": \"dc675...\"}`. 3. Máy chủ đối chiếu mã băm và thực thi truy vấn đã lưu. Bất kỳ truy vấn tùy ý nào do tin tặc tự viết đều bị máy chủ từ chối ngay lập tức vì không nằm trong danh sách trắng!"
                )
            ],
            "Kịch bản phòng thủ thực tế: Triển Khai Persisted Queries Tại Doanh Nghiệp Lớn: Khi triển khai Persisted Queries, toàn bộ các công cụ tấn công như InQL, CrackQL, Clairvoyance hay các payload DoS đều trở nên hoàn toàn vô dụng, vì máy chủ không còn chấp nhận bất kỳ chuỗi truy vấn động nào từ bên ngoài.",
            "Thực hành cấu hình bảo vệ toàn diện máy chủ Apollo Server trong mã nguồn Node.js/TypeScript:",
            ("typescript", """// Cấu hình làm cứng an ninh tối đa cho Apollo Server Production
import { ApolloServer } from '@apollo/server';
import depthLimit from 'graphql-depth-limit';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  // 1. Tắt Introspection trên Production
  introspection: process.env.NODE_ENV !== 'production',
  // 2. Giới hạn độ sâu truy vấn tối đa 5 tầng để chống DoS
  validationRules: [depthLimit(5)],
  // 3. Che giấu thông điệp lỗi chi tiết khỏi client
  formatError: (formattedError, error) => {
    return { message: "Yêu cầu không hợp lệ hoặc lỗi máy chủ nội bộ." };
  },
});"""),
            ["Luôn áp dụng nguyên tắc Safe-listing (Persisted Queries) cho các ứng dụng di động và web thương mại quan trọng.", "Đảm bảo đội ngũ phát triển tuân thủ quy trình kiểm thử phân quyền tự động cho từng Resolver."],
            ["Phòng thủ GraphQL đòi hỏi chiến lược đa lớp: Khóa Schema, Giới hạn tài nguyên và Xác thực phân quyền.", "Persisted Queries là lá chắn tối thượng biến GraphQL thành hệ thống đóng an toàn như REST.", "Kiểm tra kỹ lưỡng logic phân quyền trong từng hàm Resolver là nền tảng cốt lõi."],
            [
                {"question": "Giải pháp nào lưu sẵn các truy vấn hợp lệ dưới dạng mã băm trên máy chủ và từ chối mọi truy vấn động tùy ý của hacker?", "type": "MULTIPLE_CHOICE", "options": ["Persisted Queries (Safe-listing)", "SQL Injection", "CORS", "WebSockets"], "correct_index": 0, "explanation": "Persisted Queries (Truy vấn lưu sẵn / Safe-listing)."},
                {"question": "Quy tắc kiểm tra nào đo lường tổng chi phí tính toán của các trường để chặn truy vấn quá tải trước khi thực thi?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Query Cost Analysis", "Query Complexity", "query cost analysis"]}], "explanation": "Query Cost Analysis / Query Complexity."},
                {"question": "Chỉ cần tắt tính năng Introspection là hệ thống GraphQL đã an toàn 100% trước mọi cuộc tấn công?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Tắt Introspection chỉ là bước đầu tiên; hệ thống vẫn đối mặt với DoS, BOLA, Injection và CSRF."}
            ]
        )
    ]

    for (pos, title, summary, v_url, obj_pts, theory_secs, att_def, lab_inst, code_snip, pits, sums, q_json) in configs_part2:
        l = {
            "position": pos,
            "title": title,
            "summary": summary,
            "duration_minutes": 35,
            "video_url": v_url,
            "markdown_content": generate_lesson_markdown(
                lesson_num=f"5.{pos}",
                title=title,
                objective_points=obj_pts,
                theory_sections=theory_secs,
                attack_defense_section=att_def,
                lab_instructions=lab_inst,
                code_snippet=code_snip,
                pitfalls=pits,
                summary_points=sums,
                video_url=v_url,
                quiz_json=q_json,
            )
        }
        validate_lesson_data(l)
        lessons.append(l)

    return lessons


if __name__ == "__main__":
    ls = get_chapter_5_lessons()
    print(f"Generated {len(ls)} lessons for Chapter 5.")
    for l in ls:
        wc = count_vietnamese_words(l["markdown_content"])
        print(f"  - {l['title'][:40]}: {wc} words")
