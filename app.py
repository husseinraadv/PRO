from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
import os

app = Flask(__name__)

# إعداد الاتصال بـ Google Sheets
def load_products():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/1Bg0s6LuuGoIX3Ni-UT-KYiTjff6t6PP_2Zrxx-d4sSg/edit#gid=0"
    sheet = client.open_by_url(sheet_url).sheet1
    return sheet.get_all_records()

# إعداد البرومبت
prompt = PromptTemplate(
    input_variables=["user_input", "product_data"],
    template="""
أنت بوت شركة الأماني، تتكلم باللهجة العراقية وترد باختصار وواقعية.

هاي المنتجات المتوفرة حالياً:

{product_data}

رسالة الزبون: {user_input}

إذا شفت منتج يطابق طلب الزبون، رد عليه بالتنسيق التالي:

📦 الاسم: [اسم المنتج]  
📱 المواصفات: [مواصفات المنتج]  
💵 السعر: [السعر] دولار  
📦 الكمية: [الكمية]  
🔗 رابط الشراء: [الرابط]

إذا ما لقيت منتج مناسب، قل له: "ما متوفر حاليًا، نكدر نبلغك أول ما يوصل."
"""
)

# إعداد LLM
llm = ChatGroq(
    groq_api_key="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",
    model_name="llama3-70b-8192",
    temperature=0.2
)

chain = LLMChain(llm=llm, prompt=prompt)

@app.route("/")
def home():
    return "⚡ Webhook is live"

@app.route("/chat", methods=["GET"])
def chat_page():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def handle_chat():
    try:
        user_input = request.json.get("message", "").strip().lower()

        # ردود التحية الثابتة
        greetings = ["السلام عليكم", "مرحبا", "هلا", "اهلا", "شلونك", "صباح الخير", "مساء الخير"]
        for greet in greetings:
            if greet in user_input:
                return jsonify({"reply": "وعليكم السلام ورحمة الله 😊 وياك بوت الأماني! شنو تحب تشتري اليوم؟"})

        # باقي الرسائل
        products = load_products()
        summary = "\n".join([
            f"{p['الاسم التجاري للمنتج']} - {p['المواصفات']} - {p['السعر']} دولار - {p['الكمية المتوفرة']} قطعة - {p['رابط الشراء']}"
            for p in products
        ])
        response = chain.invoke({"user_input": user_input, "product_data": summary})
        return jsonify({"reply": response['text']})
    except Exception as e:
        print("خطأ:", e)
        return jsonify({"reply": "⚠️ صار خطأ، جرب تراسلنا بعد شوي."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
