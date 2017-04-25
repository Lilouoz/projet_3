<?php 

include_once ('config.php');


 

//modele : Acces au donnes


/******** GERE PAR LE MANAGER ***********/
try
{
	$db = new PDO('mysql:host=localhost;dbname=projet_blog_p3;charset=utf8', 'root', 'root');
}
catch (Exception $e)
{
        die('Erreur : ' . $e->getMessage());
}
$query = "SELECT * FROM billets ORDER BY date_creation";

$req =$db->prepare($query);
$req->execute();
// PDO::FETCH_ASSOC = retourne un tableau indexé par le nom de la colonne comme retourné dans le jeu de résultats
while ($row = $req->fetch(PDO::FETCH_ASSOC)) {
	
	$billet = array(
		'id'=> $row['id'],
		'image'=> $row['image'],
		'alt'=> $row['alt'],
		'titre'=> $row['titre'],
		'contenu'=> $row['contenu'],
		'auteur'=> $row['auteur'],
		'date_creation'=> $row['date_creation'],
	); 
	//creation objet $billet 
 /*
	{
      $billet = new Billet($row)
}
    return $$billet
	*/
 }
  
  
/*********** fin du manager **********/


/* 


$manager = new BilletsManager();
$billets = $manager->getAll();


*/

//traitement 
//vue
;?>

	<!DOCTYPE html>
	<html>

	<!-- on récupere le headers  -->
	<?php include_once(PARTIAL.'header.php'); ?>



		<body>


			<?php include_once(PARTIAL.'header_top.php'); ?>

				<?php include_once(PARTIAL.'menu.php'); ?>

					<?php include_once(PARTIAL.'banner.php'); ?>

						<?php include (PARTIAL.'container_corps.php'); ?>

							<?php include_once(PARTIAL.'footer.php'); ?>

								<?php include (PARTIAL.'script.php'); ?>


		</body>

	</html>