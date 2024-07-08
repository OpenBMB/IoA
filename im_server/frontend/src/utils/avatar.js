function stringTo1_100(text) {
  // Create a hash from the text using MD5
  const hash = text.split("").reduce((acc, char) => {
    return acc + char.charCodeAt(0); // Sum of char codes
  }, 0);

  // Step 2: Map the hash to the range 1-100
  // Since char codes can vary greatly, use modulus to fit within a smaller range
  const range = 100; // 100 is the target range

  // Map the hash to 0-(range-1) and then shift to 1-range
  const mappedValue = (hash % range) + 1;

  return mappedValue;
}

function getAvatar(name) {
  return `https://avatar.iran.liara.run/public/${stringTo1_100(name)}`;
}

export default getAvatar;
