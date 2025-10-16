from fastapi import FastAPI
from pydantic import BaseModel
from analyzer import load_data, generate_explanation

app = FastAPI(title="POC9 High Bill Inquiry API")

customers, bills, intervals = load_data()

class ExplainRequest(BaseModel):
    customer_id: int

@app.post("/explain")
def explain(req: ExplainRequest):
    try:
        result = generate_explanation(req.customer_id, customers, bills, intervals)
        # attach bill totals for context
        prev = bills[(bills["customer_id"]==req.customer_id) & (bills["period"]=="previous")].iloc[0].to_dict()
        curr = bills[(bills["customer_id"]==req.customer_id) & (bills["period"]=="current")].iloc[0].to_dict()
        result["bill_previous"] = prev
        result["bill_current"] = curr
        return {"ok": True, "data": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
