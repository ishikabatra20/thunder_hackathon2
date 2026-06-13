function outer(x){
    return function(y){
        return x+y;
    };
}

let fn = outer(10);
console.log(fn(5));

let arr = [1,2,3];
arr.reverse();
console.log(arr.join(","));

let s = "hello";
console.log(s.replace("h","y"));

for(let i=0;i<3;i++){
    console.log(i);
}