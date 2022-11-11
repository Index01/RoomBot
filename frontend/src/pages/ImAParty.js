import WhereDaParty from '../components/whereDaParty.js';
import IAmAParty from '../components/iAmTheParty.js';
import "../styles/RoomDataTable.css";
import React from 'react';


const PartyFinder = () => {
    return(
        <div className="componentContainer">
            <div className="AppHeader">
	         <img src="roombaht_header.png" alt="RoomBaht9000" />
            </div>
            <div className="DTApp"> 
              <IAmAParty/>
            </div>
            <div className="DTApp"> Where Da Party Is At? 
              <WhereDaParty/>
            </div>
        </div>
    );
};

export default PartyFinder;
