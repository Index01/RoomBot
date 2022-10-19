import RoomDataTable from '../components/dasDataTable.js';
import MyRoomsTable from '../components/myRooms.js';
import "../styles/RoomDataTable.css";
import React from 'react';


const RoomSelekta = () => {
    return(
        <span className="componentContainer">

            <div className="AppHeader">
              <p>
                 Select it. Swap it. Wtvr.
              </p>
            </div>
             
            <div className="DTApp">
              <RoomDataTable/>
            </div>
            <div className="DTApp"> My Rooms
              <MyRoomsTable/>
            </div>
        </span>
    );
};

export default RoomSelekta;
