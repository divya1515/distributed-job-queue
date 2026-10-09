from pydantic import BaseModel,EmailStr,Field

class ClientRegister(BaseModel):
    
    username :str=Field(...,min_length=3,max_length=30)
   
