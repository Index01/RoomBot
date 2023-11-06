
import RoombotAdmin from '../components/admin.js';
import BasicVis from '../components/adminMetrics.js';
import "../styles/RoombotAdmin.css";
import React from 'react';
import { Toaster } from 'react-hot-toast';

const AppAdmin = () => {
    return(
        <div className="componentContainer">

            <div className="AppHeader">
	         <img src="roombaht_header.png" alt="RoomBaht9000" />
            </div>

            <div className="DTApp"> Roombot Metrics
              <BasicVis/>
            </div>

            <div className="DTApp"> Roombot Admin
              <RoombotAdmin/>
            </div>
            <Toaster />
        </div>
    );
};

export default AppAdmin;
