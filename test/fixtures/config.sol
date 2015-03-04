contract owned {
    function owned() { owner = msg.sender; }
    address owner;
}

// Use "is" to derive from another contract. Derived contracts can access all members
// including private functions and storage variables.
contract mortal is owned {
    function kill() { if (msg.sender == owner) suicide(owner); }
}

contract Config is owned, mortal {
    event ServiceChanged(uint indexed id);
    function register(uint id, address service) {
        if (tx.origin != owner)
            return;
        services[id] = service;
        ServiceChanged(id);
    }

    function unregister(uint id) {
        if (msg.sender != owner && services[id] != msg.sender)
            return;
        services[id] = address(0);
        ServiceChanged(id);
    }

    function lookup(uint service) constant returns(address a) {
        return services[service];
    }

    mapping (uint => address) services;
}
