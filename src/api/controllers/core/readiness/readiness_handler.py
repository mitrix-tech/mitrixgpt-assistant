from fastapi import APIRouter, status

from api.schemas.status_ok_schema import StatusOkResponseSchema


router = APIRouter()


@router.get(
    "/-/ready",
    response_model=StatusOkResponseSchema,
    status_code=status.HTTP_200_OK,
    tags=["Healthcheck"]
)
async def readiness():
    """
    This route can be used as a readinessProbe for Kubernetes. By default, the
    route will always response with an OK status and the 200 HTTP code as soon
    as the service is up.
    """

    return {"statusOk": True}
