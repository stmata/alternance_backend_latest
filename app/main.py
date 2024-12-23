from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.eda_route import eda_route
from app.routes.email_route import email_router
from app.routes.retrieve_blop_route import retrieve_filerouter
from app.routes.pdf_input_summarize_route import pdf_input_summarize_router
from app.routes.predict_jobs_route import predict_jobs_router
from app.routes.user_likes_predictions_history import history_router
from app.routes.finalize_porcess_route import finalize_process_router



app = FastAPI()

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