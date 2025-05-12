from mangum import Mangum
from emaillm import app  # existing FastAPI instance

handler = Mangum(app)
