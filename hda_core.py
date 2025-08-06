from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class BirthDataModel(BaseModel):
    birthDate: str
    birthTime: str
    birthPlace: str


@app.post("/generate-details")
def generate_details(data: BirthDataModel):
    msg = "Hello beautiful soul!"
    hd_info = {"type": "Manifesting Generator",
               "authority": "Sacral",
               "profile": "1/3"}
    gk_info = {"life_work": 30,
               "evolution": 29}
    a_info = {"sun": "Aquarius",
              "moon": "Gemini",
              "rising": "Leo"}
    
    return {"message": msg,
            "human_design": hd_info,
            "gene_keys": gk_info,
            "astrology": a_info}
