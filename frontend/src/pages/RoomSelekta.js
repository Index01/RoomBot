import RoomDataTable from '../components/dasDataTable.js';
import MyRoomsTable from '../components/myRooms.js';
import "../styles/RoomDataTable.css";
import React from 'react';


const RoomSelekta = () => {
    return(
        <div className="componentContainer">

            <div className="AppHeader">
	         <img src="roombaht_header.png" alt="RoomBaht9000" />
            </div>
             
            <div className="DTApp"> My Rooms
              <MyRoomsTable/>
            </div>

            <div className="DTApp"> Swappable Rooms
              <RoomDataTable/>
            </div>

        </div>
    );
};

export default RoomSelekta;
