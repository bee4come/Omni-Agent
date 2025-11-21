const { Mnee } = require('@mnee/ts-sdk');

// Initialize Real SDK
// We use 'sandbox' but we don't actually broadcast in the 'transfer' command
const mnee = new Mnee({ 
  environment: 'sandbox', 
  apiKey: process.env.MNEE_API_KEY || 'mock-key' 
});

async function main() {
  const command = process.argv[2];
  const args = process.argv.slice(3);

  try {
    if (command === 'balance') {
      const address = args[0];
      try {
          // Attempt Real Network Call
          const balance = await mnee.balance(address);
          console.log(JSON.stringify(balance));
      } catch (e) {
          // Fallback Mock if network/address fails
          // This ensures the demo works even if the sandbox is down or address is new
          console.log(JSON.stringify({ 
              address, 
              amount: 100000000, 
              decimalAmount: 1000.0,
              note: "Fallback Mock Balance"
          }));
      }
    } 
    else if (command === 'transfer') {
      // args[0] is recipients JSON string
      // args[1] is WIF (ignored in mock)
      
      const recipients = JSON.parse(args[0]);
      
      // MOCK PAYMENT EXECUTION
      // We skip the actual mnee.transfer() call to avoid needing real UTXOs
      
      const mockTicketId = "ticket-" + Date.now().toString(16) + "-" + Math.floor(Math.random()*10000);
      
      const response = {
        ticketId: mockTicketId,
        status: 'SUCCESS',
        rawtx: "01000000...",
        mock: true
      };
      
      console.log(JSON.stringify(response));
    }
    else if (command === 'config') {
       try {
         const config = await mnee.config();
         console.log(JSON.stringify(config));
       } catch(e) {
         console.log(JSON.stringify({
            approver: "mock-approver",
            fees: [{min:0, max:999, fee:1}]
         }));
       }
    }
  } catch (error) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

main();
