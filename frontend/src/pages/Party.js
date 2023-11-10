import "../styles/party.css";
import { TheParties } from "../components/party.js";
import React from "react";
import { Toaster } from 'react-hot-toast';

export function PartyFinder() {
  return(
    <>
    <div className="componentContainer">
      <div className="DTApp partyApp">
	<span className="display-3">Where da party at tho</span>
        <TheParties />
      </div>
    </div>
    <Toaster/>
    </>
  );
};
