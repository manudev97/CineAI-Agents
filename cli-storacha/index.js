import fs from 'fs/promises';

async function main() {
    // create client
    const client = await create();

    // log into account & replace with your email
    const account = await Client.login('username@email.com');
    
    // create space
    const space = await client.createSpace('ai-agent-langchain', { account });
    console.log(`Current space set to: ${space.did()}`);

    // read file 
    const filePath = '../web-scraper-agent/faiss_index.idx';
    const fileContent = await fs.readFile(filePath);
    
    // convert file to blob
    const file = new File([fileContent], 'faiss_index.idx');

    // upload file 
    const cid = await client.uploaadFile(file);
    console.log(`File uploaded succesfully. CID: ${cid}`);
}

// return errores
main().catch((err) => {
    console.error('Error:', err);
});