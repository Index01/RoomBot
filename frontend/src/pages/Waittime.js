import "../styles/WaitTimes.css";
import { TheTimers, HowLongTho } from "../components/waittimes.js";
import React from "react";
import { Toaster } from 'react-hot-toast';

export function Waittime() {
  return(
    <div className="componentContainer">
      <div className="AppHeader">
	    <img src="/roombaht_header.png" alt="RoomBaht9000" />
      </div>

      <div className="DTApp">
        <HowLongTho />
      </div>

      <div className="AppNav">
	      <a href="/waittime">Wait Times</a>
      </div>
    </div>
  );
};

export function WaittimeList() {
  return(
    <>
    <div className="componentContainer">

      <div className="AppHeader">
          <img src="/roombaht_header.png" alt="RoomBaht9000" />
      </div>

      <div className="DTApp">Wait Times for the people because the people need to Wait
        <TheTimers />
      </div>

    </div>
    <Toaster/>
    </>
  );
};
