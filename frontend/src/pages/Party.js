import "../styles/RoombotAdmin.css";
import { TheParties } from "../components/party.js";
import React from "react";
import { Toaster } from 'react-hot-toast';

export function PartyFinder() {
  return(
    <>
    <div className="componentContainer">
      <div className="AppHeader">
	<img src="/roombaht_header.png" alt="RoomBaht9000" />
      </div>
      <div className="DTApp">Where da party at tho
        <TheParties />
      </div>
    </div>
    <Toaster/>
    </>
  );
};
