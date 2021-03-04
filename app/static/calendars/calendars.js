function generateAvailability(startTime, date, interval, busy=null) {
    const period = 'm';
    let d = moment("23:59:59", "HH:mm:ss").diff(moment(startTime, "HH:mm:ss"), 'minutes');
    const periodsInADay = moment.duration(d, 'minutes').as(period);

    const times = [];
    const startTimeMoment = moment(startTime, 'hh:mm:ssZ');

    for (let i = 0; i <= periodsInADay; i += interval) {
        startTimeMoment.add(i === 0 ? 0 : interval, period);
        if (busy !== null && busy.length > 0){
            let currentDateTime = moment(date).format('YYYY-MM-DD ' + startTimeMoment.format('HH:mm:ss') + 'Z');
            let exists = busy.some(x => moment(currentDateTime).isBetween(moment(JSON.stringify(x['start'])), moment(JSON.stringify(x['end']))) ||
                            moment(currentDateTime).add(interval, period).isBetween(moment(JSON.stringify(x['start'])), moment(JSON.stringify(x['end']))) ||
                            moment(currentDateTime).isSame(moment(JSON.stringify(x['start']))) ||
                            moment(currentDateTime).isSame(moment(JSON.stringify(x['end']))));
            if (!exists)
            {
                times.push(startTimeMoment.format('hh:mm a'));
            }
        }
        else{
            times.push(startTimeMoment.format('hh:mm a'));
        }
    }
    return [times];
}

function generateTimes(interval, military=false, availability=[]) {
    let x = interval
    let times = []; // time array
    let start = 0; // start time
    let ap = ['am', 'pm']; // AM-PM

    // Availability
    let a_start = 7;
    let a_stop = 24;
    //availability = [9,18];

    //loop to increment the time and push results in array
    for (let i = 0; start < 24 * 60; i++) {
        let hh = Math.floor(start / 60); // getting hours of day in 0-24 format

        // Check military time
        // h is 12-hour format, hh is 24 hour format
        let h = "0" + hh;

        if (military === false) {
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