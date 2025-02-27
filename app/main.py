from fastapi import FastAPI
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from app.routes.eda_route import eda_route
from app.routes.email_route import email_router
from app.routes.retrieve_blop_route import retrieve_filerouter
from app.routes.pdf_input_summarize_route import pdf_input_summarize_router
from app.routes.predict_jobs_route import predict_jobs_router
from app.routes.user_likes_predictions_history import history_router
from app.routes.finalize_porcess_route import finalize_process_router



app = FastAPI(docs_url=None, redoc_url=None, version='0.1')

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(retrieve_filerouter)
app.include_router(eda_route)
app.include_router(email_router)
app.include_router(pdf_input_summarize_router)
app.include_router(predict_jobs_router)
app.include_router(history_router)
app.include_router(finalize_process_router)


# Launch the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
