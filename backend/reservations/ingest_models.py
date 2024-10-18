"""Datatypes for importing guest and room lists"""
# we don't need a StaffImport model because that table is directly translated to the db table

from typing import Optional
from pydantic import BaseModel, Field

class SecretPartyGuestIngest(BaseModel):
    """Required fields imported from SecretParty CSV
    """
    ticket_code: str  # transaction code for purchase/transfer
    last_name: str
    first_name: str
    email: str
    product: str  # product code, eg name of addon for event, or hotel sku
    transferred_from_code: Optional[str] = None
    type: Optional[str] = None


class RoomPlacementListIngest(BaseModel):
    """Expected fields in the room spreadsheet
    NOTE: not all of these columns may be used!
    """
    placement_verified: Optional[str] = Field(None, alias='Placement Verified')
    room: int = Field(alias='Room')
    room_type: str = Field(alias='Room Type')
    room_features: Optional[str] = Field(alias='Room Features (Accessibility, Lakeview, Smoking)')
    first_name_resident: Optional[str] = Field(alias='First Name (Resident)')
    last_name_resident: Optional[str] = Field(alias='Last Name (Resident)')
    secondary_name: Optional[str] = Field(alias='Secondary Name')
    # check in and out are currently strings, not dates
    check_in_date: Optional[str] = Field(alias='Check-in Date')
    check_out_date: Optional[str] = Field(alias='Check-out Date')
    placed_by: Optional[str] = Field(alias='Placed By')
    ticket_id_in_secret_party: Optional[str] = Field(alias='Ticket ID in SecretParty')

    class Config:
        populate_by_name = True  # allows data to be populated in the model by field names, not just aliases
        extra = 'ignore'  # the model will ignore any additional fields not specified in the model during initialization
