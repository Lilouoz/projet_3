<?php 
init_set ('display_errors', 'on');
error_reporting(E_ALL);

function loadClass($class)
{
	include("entity/".$class.'Class.php');
}

spl_autoload_register('loadClass');
?>