const d = require('./compressed_ranks.json');
const dance2026 = d['dance_2026'];
const entries = Object.entries(dance2026).map(([s,c]) => ({score:+s, cum:c})).sort((a,b) => b.score - a.score);

function interp(arr, target, keyS, keyR) {
    if(!arr || !arr.length) return null;
    if(target >= arr[0][keyS]) return arr[0][keyR];
    if(target <= arr[arr.length-1][keyS]) return arr[arr.length-1][keyR];
    for(let i=0; i<arr.length-1; i++) {
        if(arr[i][keyS] > target && arr[i+1][keyS] <= target) {
            const t = (target - arr[i][keyS]) / (arr[i+1][keyS] - arr[i][keyS]);
            return Math.round(arr[i][keyR] + t * (arr[i+1][keyR] - arr[i][keyR]));
        }
    }
    return null;
}

const rank = interp(entries, 515.00, 'score', 'cum');
console.log('Rank for 515.00:', rank);
console.log('max score:', entries[0].score, 'min score:', entries[entries.length-1].score);
console.log('total entries:', entries.length);

// Find where 515 falls
for(let i=0; i<entries.length-1; i++) {
    if(entries[i].score > 515 && entries[i+1].score <= 515) {
        console.log('Found bracket: entries['+i+'].score='+entries[i].score+' cum='+entries[i].cum+' | entries['+(i+1)+'].score='+entries[i+1].score+' cum='+entries[i+1].cum);
        break;
    }
}
