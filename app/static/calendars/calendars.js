function generateTimes(interval, military=false, availability=[]) {
    let x = interval
    let times = []; // time array
    let start = 0; // start time
    let ap = ['am', 'pm']; // AM-PM

    // Availability
    let a_start = 0;
    let a_stop = 24;
    //availability = [9,18];

    //loop to increment the time and push results in array
    for (let i = 0; start < 24 * 60; i++) {
        let hh = Math.floor(start / 60); // getting hours of day in 0-24 format

        // Check military time
        let h = "0" + hh;
        if (military !== true) {
            if ((hh % 12) === 0) {
                h = 12
            } else {
                h = hh;
            }

            if (hh > 12) {
                h = hh - 12;
            }
        }
        let mm = (start % 60); // getting minutes of the hour in 0-55 format

        // Check availability
        if (availability.length > 0){
            a_start = availability[0];
            a_stop = availability[1];

            if (a_start < hh < a_stop){
                times[i] = h.toString().slice(-2) + ':' + ("0" + mm).slice(-2) + ' ' + ap[Math.floor(hh / 12)]; // pushing data in array in [00:00 - 12:00 AM/PM format]
                start = start + x;
            }
        }
        else {
            times[i] = h.toString().slice(-2) + ':' + ("0" + mm).slice(-2) + ' ' + ap[Math.floor(hh / 12)]; // pushing data in array in [00:00 - 12:00 AM/PM format]
            start = start + x;
        }
    }
    return times
}