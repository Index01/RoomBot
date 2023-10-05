
import RoombotAdmin from '../components/admin.js';
import "../styles/RoombotAdmin.css";
import React from 'react';


const AppAdmin = () => {
    return(
        <div className="componentContainer">

            <div className="AppHeader">
	         <img src="roombaht_header.png" alt="RoomBaht9000" />
            </div>
             
            <div className="DTApp"> Roombot Admin 
              <RoombotAdmin/>
            </div>

        </div>
    );
};

export default AppAdmin;
