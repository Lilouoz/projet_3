<?php
class PDOFactory
{
  public static function getMysqlConnexion()
  {
    $db = new PDO('mysql:host=localhost;dbname=projet_blog_p3', 'root', 'root');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    return $db;
  }
  
  public static function getPgsqlConnexion()
  {
    $db = new PDO('pgsql:host=localhost;dbname=tests', 'root', '');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    return $db;
  }
}