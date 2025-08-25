import sys, re, json, os, base64
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from config import DI_ENDPOINT, DI_KEY

# Default to phase1_data/form.jpg if no argument provided
if len(sys.argv) >= 2:
    IMG = sys.argv[1]
else:
    IMG = os.path.join(os.path.dirname(__file__), "phase1_data", "form.jpg")
    print(f"[info] No path provided; using default: {IMG}")

# Use DI directly with JSON output to access pages/lines/words
with open(IMG, "rb") as f:
    file_bytes = f.read()

client = DocumentIntelligenceClient(DI_ENDPOINT, AzureKeyCredential(DI_KEY))
poller = client.begin_analyze_document(
    model_id="prebuilt-layout",
    body={"base64Source": base64.b64encode(file_bytes).decode("utf-8")},
    output_content_format="markdown",
    string_index_type="unicodeCodePoint",
)
result = poller.result()
text = result.content or ""
raw = result.as_dict()

def center(poly):
    xs = poly[::2]; ys = poly[1::2]
    return sum(xs)/len(xs), sum(ys)/len(ys)

aru = raw.get("analyzeResult", {})
pages = aru.get("pages", [])

if pages:
    for p in pages:
        words = p.get("words", [])
        lines = p.get("lines", [])
        print(f"\n=== Page {p.get('pageNumber')} ===")

        def same_row_tokens(line, tol=0.15):
            _, ly = center(line["polygon"])
            row = []
            for w in words:
                wx, wy = center(w["polygon"])
                if abs(wy - ly) < tol:
                    row.append((wx, w["content"]))
            row.sort()
            return [t for _, t in row]

        checks = [
            ("ID", ["ת.ז", 'ת"ז', "תעודת זהות", "מספר זהות"]),
            ("ReceiptDate", ["תאריך קבלת הטופס בקופה"]),
        ]

        for kind, candidates in checks:
            for ln in lines:
                content = ln.get("content","")
                if any(lbl in content for lbl in candidates):
                    row = same_row_tokens(ln)
                    print(f"\n[{kind}] LABEL: {content}")
                    print("ROW:", row)
                    joined = " ".join(row)
                    ids = re.findall(r"\b(\d{9})\b", joined)
                    dates = re.findall(r"\b(\d{8})\b", joined)
                    if ids:   print("CANDIDATE 9-DIGIT IDs:", ids)
                    if dates: print("CANDIDATE 8-DIGIT DATES:", dates)
else:
    # Fallback: scan text-only to find labels and nearby digits
    print("[warn] No structured pages returned; using text-only scan.")
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    def scan(kind, needles, window=2):
        for i, ln in enumerate(lines):
            if any(n in ln for n in needles):
                ctx = " ".join(lines[max(0, i-window): min(len(lines), i+window+1)])
                print(f"\n[{kind}] LABEL LINE: {ln}")
                ids = re.findall(r"\b(\d{9})\b", ctx)
                dates = re.findall(r"\b(\d{8})\b", ctx)
                if ids:   print("CANDIDATE 9-DIGIT IDs:", ids)
                if dates: print("CANDIDATE 8-DIGIT DATES:", dates)
    scan("ID", ["ת.ז", 'ת"ז', "תעודת זהות", "מספר זהות"])
    scan("ReceiptDate", ["תאריך קבלת הטופס בקופה"]) 
