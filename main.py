
from domain_detection.pipeline.training_pipeline import TrainPipeline
from fastapi import FastAPI, File, UploadFile, Request
from domain_detection.constant.training_pipeline import SAVED_MODEL_DIR
from uvicorn import run as app_run
from starlette.responses import RedirectResponse
from fastapi.responses import Response
from domain_detection.ml.model.estimator import ModelResolver,TargetValueMapping
from domain_detection.utils.main_utils import load_object
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import pandas as pd
from dotenv import find_dotenv, load_dotenv
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
APP_HOST = os.getenv("APP_HOST")
APP_PORT = os.getenv("APP_POST")

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")


@app.get("/train")
async def train_route():
    try:
        train_pipeline = TrainPipeline()
        if train_pipeline.is_pipeline_running:
            return Response("Training pipeline is already running.")
        train_pipeline.run_pipeline()
        return Response("Training successful !!")
    except Exception as e:
        return Response(f"Error Occurred! {str(e)}")


@app.post("/predict")
async def predict_route(request: Request, file: UploadFile = File(...)):
    try:
        # Read data from user-uploaded CSV file and convert to a DataFrame
        df = pd.read_csv(file.file)

        # Load the trained model
        model_resolver = ModelResolver(model_dir=SAVED_MODEL_DIR)
        if not model_resolver.is_model_exists():
            return Response("Model is not available")
        best_model_path = model_resolver.get_best_model_path()
        model = load_object(file_path=best_model_path)

        # Perform predictions using the loaded model
        y_pred = model.predict(df)

        # Assuming the model's predictions are a list or array
        df['predicted_column'] = y_pred
        df['predicted_column'].replace(TargetValueMapping().reverse_mapping(), inplace=True)

        # Convert DataFrame to JSON and return it as a JSON response
        return JSONResponse(content=df.to_dict(orient="records"))

    except Exception as e:
        return JSONResponse(content={"error": f"An error occurred: {str(e)}"}, status_code=500)


if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)
