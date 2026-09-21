# import pytest


# @pytest.mark.asyncio
# async def test_workshop_requires_authentication(client):
#     response = await client.post(
#         "/api/v1/cars/00000000-0000-0000-0000-000000000000/workshop",
#         json={
#             "note": "Engine problem",
#         },
#     )

#     assert response.status_code == 401


# @pytest.mark.asyncio
# async def test_back_in_service_requires_authentication(client):
#     response = await client.post(
#         "/api/v1/cars/00000000-0000-0000-0000-000000000000/back-in-service",
#     )

#     assert response.status_code == 401
