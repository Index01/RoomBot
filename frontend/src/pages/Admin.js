
import RoombotAdmin from '../components/admin.js';
import BasicVis from '../components/adminMetrics.js';
import "../styles/RoombotAdmin.css";
import React from 'react';
import { createContext } from 'react';
import { Toaster } from 'react-hot-toast';

const AppAdmin = () => {
  var updateMetrics = 0;
  const onChange = () => {
    updateMetrics++;
  }
    return(
        <div className="componentContainer">

            <div className="AppHeader">
	         <img src="roombaht_header.png" alt="RoomBaht9000" />
            </div>

            <div className="DTApp"> Roombot Metrics
              <BasicVis updateMetrics={updateMetrics}/>
            </div>

            <div className="DTApp"> Roombot Admin
              <RoombotAdmin onChange={onChange}/>
            </div>
            <Toaster />
        </div>
    );
};

export default AppAdmin;
