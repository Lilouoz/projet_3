<?php
class BddManager
{
    protected $db;
    private $host      = "localhost";
    private $login     = "root";
    private $password  = "root";
    public function __construct()
    {
        $db = new PDO('mysql:host='.$this->host.';dbname=projet_blog_p3;charset=utf8', $this->login, $this->password);
        $this->db = $db;
    }
    public function deleteById($table, $entity_id)
    {
        $db = $this->db;
        $req = $db->prepare("DELETE FROM ".$table." WHERE id = ".$entity_id);
        $req->execute();
    }
}